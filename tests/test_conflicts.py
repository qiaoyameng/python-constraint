import pytest

import constraint
from constraint import ConflictReport


def build_two_group_problem():
    problem = constraint.Problem()
    problem.addVariables(["a", "b"], [1, 2])
    problem.addConstraint(lambda a: a == 1, ["a"], label="a-is-one")
    problem.addConstraint(lambda a: a == 2, ["a"], label="a-is-two")
    problem.addConstraint(lambda b: b == 1, ["b"], label="b-is-one")
    problem.addConstraint(lambda b: b == 2, ["b"], label="b-is-two")
    return problem


def test_satisfiable_problem_returns_status_not_empty_conflict():
    problem = constraint.Problem()
    problem.addVariables(["a", "b"], [1, 2])
    problem.addConstraint(lambda a: a == 1, ["a"], label="a-is-one")
    problem.addConstraint(lambda b: b == 2, ["b"], label="b-is-two")
    report = problem.findMinimalUnsatisfiableSubset()
    assert report.status == ConflictReport.SATISFIABLE
    assert report.conflict == ()
    assert report.solution == {"a": 1, "b": 2}
    assert report.complete


def test_background_unsatisfiable_with_unlabeled_constraints():
    problem = constraint.Problem()
    problem.addVariable("a", [1, 2])
    problem.addConstraint(lambda a: a == 1, ["a"])
    problem.addConstraint(lambda a: a == 2, ["a"])
    problem.addConstraint(lambda a: a in (1, 2), ["a"], label="harmless")
    report = problem.findMinimalUnsatisfiableSubset()
    assert report.status == ConflictReport.BACKGROUND_UNSATISFIABLE
    assert report.conflict == ()


def test_background_unsatisfiable_with_labeled_background():
    problem = constraint.Problem()
    problem.addVariable("a", [1, 2])
    problem.addConstraint(lambda a: a == 1, ["a"], label="bg-one")
    problem.addConstraint(lambda a: a == 2, ["a"], label="bg-two")
    problem.addConstraint(lambda a: a in (1, 2), ["a"], label="candidate")
    report = problem.findMinimalUnsatisfiableSubset(
        background=["bg-one", "bg-two"]
    )
    assert report.status == ConflictReport.BACKGROUND_UNSATISFIABLE
    assert report.conflict == ()


def test_two_disjoint_contradiction_groups_pick_either():
    problem = build_two_group_problem()
    report = problem.findMinimalUnsatisfiableSubset()
    assert report.status == ConflictReport.UNSATISFIABLE
    assert report.conflict in (
        ("a-is-one", "a-is-two"),
        ("b-is-one", "b-is-two"),
    )


def test_removing_any_reported_item_makes_it_satisfiable():
    problem = build_two_group_problem()
    report = problem.findMinimalUnsatisfiableSubset()
    assert report.status == ConflictReport.UNSATISFIABLE
    for dropped in report.conflict:
        check = constraint.Problem()
        check.addVariables(["a", "b"], [1, 2])
        for constraint_, variables, label in problem._constraints:
            if label is None or (label in report.conflict and label != dropped):
                check.addConstraint(constraint_, variables, label=label)
        assert check.getSolution() is not None


def test_unlabeled_constraints_always_apply():
    problem = constraint.Problem()
    problem.addVariables(["a", "b"], [1, 2])
    problem.addConstraint(lambda a: a == 1, ["a"])
    problem.addConstraint(lambda b: b == 1, ["b"], label="b-is-one")
    problem.addConstraint(lambda b: b == 2, ["b"], label="b-is-two")
    report = problem.findMinimalUnsatisfiableSubset()
    assert report.status == ConflictReport.UNSATISFIABLE
    assert report.conflict == ("b-is-one", "b-is-two")


def test_explicit_candidates_leave_others_as_background():
    problem = build_two_group_problem()
    report = problem.findMinimalUnsatisfiableSubset(
        candidates=["a-is-one", "a-is-two"]
    )
    assert report.status == ConflictReport.UNSATISFIABLE
    assert report.conflict == ("a-is-one", "a-is-two")


def test_trials_use_independent_domain_state():
    problem = constraint.Problem()
    problem.addVariable("x", [1, 2, 3])
    problem.addConstraint(
        constraint.InSetConstraint([1]), ["x"], label="only-one"
    )
    problem.addConstraint(
        constraint.NotInSetConstraint([1]), ["x"], label="never-one"
    )
    report = problem.findMinimalUnsatisfiableSubset()
    assert report.status == ConflictReport.UNSATISFIABLE
    assert report.conflict == ("only-one", "never-one")
    # preProcess() removals done while testing subsets must not leak
    # into the stored problem state.
    assert list(problem._variables["x"]) == [1, 2, 3]
    assert problem.getSolution() is None


def test_domain_state_not_leaking_between_trials():
    # If preProcess() deletions leaked across trials, dropping
    # "never-one" would still see x reduced by it and could wrongly
    # report the remaining set as unsatisfiable.
    problem = constraint.Problem()
    problem.addVariable("x", [1, 2, 3])
    problem.addConstraint(
        constraint.NotInSetConstraint([2, 3]), ["x"], label="never-two-three"
    )
    problem.addConstraint(
        constraint.InSetConstraint([2]), ["x"], label="only-two"
    )
    report = problem.findMinimalUnsatisfiableSubset()
    assert report.status == ConflictReport.UNSATISFIABLE
    assert report.conflict == ("never-two-three", "only-two")


def test_budget_exhausted_during_minimization():
    problem = build_two_group_problem()
    # Budget covers the background and full-problem checks only.
    report = problem.findMinimalUnsatisfiableSubset(max_checks=2)
    assert report.status == ConflictReport.INCOMPLETE
    assert not report.complete
    assert report.conflict == (
        "a-is-one",
        "a-is-two",
        "b-is-one",
        "b-is-two",
    )
    assert report.pending == (
        "a-is-one",
        "a-is-two",
        "b-is-one",
        "b-is-two",
    )
    assert report.checks == 2


def test_budget_exhausted_before_any_evidence():
    problem = build_two_group_problem()
    report = problem.findMinimalUnsatisfiableSubset(max_checks=0)
    assert report.status == ConflictReport.INCOMPLETE
    assert report.conflict is None
    assert report.checks == 0


def test_budget_partial_minimization_keeps_known_unsat_subset():
    problem = build_two_group_problem()
    # One minimization step fits in the budget.
    report = problem.findMinimalUnsatisfiableSubset(max_checks=3)
    assert report.status == ConflictReport.INCOMPLETE
    assert report.conflict is not None
    assert len(report.pending) == 3
    # The reported subset is still known to be unsatisfiable.
    check = constraint.Problem()
    check.addVariables(["a", "b"], [1, 2])
    for constraint_, variables, label in problem._constraints:
        if label in report.conflict:
            check.addConstraint(constraint_, variables, label=label)
    assert check.getSolution() is None


def test_duplicated_label_rejected():
    problem = constraint.Problem()
    problem.addVariable("a", [1, 2])
    problem.addConstraint(lambda a: a == 1, ["a"], label="dup")
    with pytest.raises(ValueError):
        problem.addConstraint(lambda a: a == 2, ["a"], label="dup")


def test_unknown_labels_rejected():
    problem = build_two_group_problem()
    with pytest.raises(ValueError):
        problem.findMinimalUnsatisfiableSubset(candidates=["nope"])
    with pytest.raises(ValueError):
        problem.findMinimalUnsatisfiableSubset(background=["nope"])


def test_label_cannot_be_background_and_candidate():
    problem = build_two_group_problem()
    with pytest.raises(ValueError):
        problem.findMinimalUnsatisfiableSubset(
            candidates=["a-is-one"], background=["a-is-one"]
        )


def test_report_repr():
    report = ConflictReport(ConflictReport.UNSATISFIABLE, conflict=["x"])
    assert "unsatisfiable" in repr(report)
    assert "'x'" in repr(report)
