import pytest

from constraint import (
    Domain,
    InSetConstraint,
    MaxSumConstraint,
    MinSumConstraint,
    MusResult,
    Problem,
)


def build_problem(spec, variables):
    problem = Problem()
    for variable, domain in variables.items():
        problem.addVariable(variable, domain)
    for label, constraint, cvariables in spec:
        problem.addConstraint(constraint, cvariables, label=label)
    return problem


def is_satisfiable(spec, variables, labels):
    kept = [item for item in spec if item[0] is None or item[0] in labels]
    problem = build_problem(kept, variables)
    return problem.getSolution() is not None


def test_satisfiable_problem_reports_status_not_empty_conflict():
    problem = Problem()
    problem.addVariable("a", [1, 2])
    problem.addConstraint(lambda a: a == 1, ["a"], label="a-is-1")
    result = problem.findMinimalUnsatisfiableSubset()
    assert result.status == MusResult.SATISFIABLE
    assert result.solution == {"a": 1}
    assert result.conflict is None
    assert result.complete


def test_background_unsatisfiable():
    problem = Problem()
    problem.addVariable("a", [1])
    problem.addConstraint(lambda a: a == 2, ["a"], label="bg")
    problem.addConstraint(lambda a: a == 1, ["a"], label="candidate")
    result = problem.findMinimalUnsatisfiableSubset(background=["bg"])
    assert result.status == MusResult.BACKGROUND_UNSATISFIABLE
    assert result.conflict == []
    assert result.complete


def test_unlabeled_constraints_are_background():
    problem = Problem()
    problem.addVariable("a", [1, 2])
    problem.addConstraint(lambda a: a == 2, ["a"])
    problem.addConstraint(lambda a: a == 1, ["a"], label="candidate")
    result = problem.findMinimalUnsatisfiableSubset()
    assert result.status == MusResult.UNSATISFIABLE
    assert result.conflict == ["candidate"]


def test_two_disjoint_conflicts_either_may_be_returned():
    variables = {"a": [1, 2], "b": [1, 2]}
    spec = [
        ("a-is-1", lambda a: a == 1, ["a"]),
        ("a-is-2", lambda a: a == 2, ["a"]),
        ("b-is-1", lambda b: b == 1, ["b"]),
        ("b-is-2", lambda b: b == 2, ["b"]),
    ]
    problem = build_problem(spec, variables)
    result = problem.findMinimalUnsatisfiableSubset()
    assert result.status == MusResult.UNSATISFIABLE
    assert set(result.conflict) in ({"a-is-1", "a-is-2"}, {"b-is-1", "b-is-2"})
    # Minimality: removing any single member makes the rest satisfiable.
    for removed in result.conflict:
        remaining = set(result.conflict) - {removed}
        assert is_satisfiable(spec, variables, remaining)


def test_minimal_conflict_with_mixed_constraints():
    variables = {"a": [1, 2, 3, 4], "b": [1, 2, 3, 4]}
    spec = [
        ("small-sum", MaxSumConstraint(3), ["a", "b"]),
        ("big-sum", MinSumConstraint(7), ["a", "b"]),
        ("a-odd", lambda a: a % 2 == 1, ["a"]),
    ]
    problem = build_problem(spec, variables)
    result = problem.findMinimalUnsatisfiableSubset()
    assert result.status == MusResult.UNSATISFIABLE
    assert set(result.conflict) == {"small-sum", "big-sum"}
    for removed in result.conflict:
        remaining = set(result.conflict) - {removed}
        assert is_satisfiable(spec, variables, remaining)


def test_candidates_selection_and_unknown_label():
    problem = Problem()
    problem.addVariable("a", [1, 2])
    problem.addConstraint(lambda a: a == 1, ["a"], label="one")
    problem.addConstraint(lambda a: a == 2, ["a"], label="two")
    result = problem.findMinimalUnsatisfiableSubset(candidates=["one"])
    assert result.status == MusResult.SATISFIABLE
    with pytest.raises(ValueError):
        problem.findMinimalUnsatisfiableSubset(candidates=["missing"])


def test_duplicate_label_rejected():
    problem = Problem()
    problem.addVariable("a", [1, 2])
    problem.addConstraint(lambda a: a == 1, ["a"], label="dup")
    with pytest.raises(ValueError):
        problem.addConstraint(lambda a: a == 2, ["a"], label="dup")


def test_budget_exhaustion_returns_incomplete_with_evidence():
    variables = {"a": [1, 2], "b": [1, 2]}
    spec = [
        ("a-is-1", lambda a: a == 1, ["a"]),
        ("a-is-2", lambda a: a == 2, ["a"]),
        ("b-is-1", lambda b: b == 1, ["b"]),
        ("b-is-2", lambda b: b == 2, ["b"]),
    ]
    problem = build_problem(spec, variables)

    # Not even the background and full checks fit in the budget.
    result = problem.findMinimalUnsatisfiableSubset(budget=1)
    assert result.status == MusResult.INCOMPLETE
    assert result.conflict is None
    assert not result.complete
    assert result.checks == 1

    # The deletion loop starts but cannot finish.
    result = problem.findMinimalUnsatisfiableSubset(budget=3)
    assert result.status == MusResult.INCOMPLETE
    assert result.conflict is not None
    # The evidence is genuinely unsatisfiable, but not promised minimal.
    assert not is_satisfiable(spec, variables, set(result.conflict))


def test_domain_state_isolated_between_checks():
    # InSetConstraint and single-variable constraints permanently remove
    # values during preprocessing; repeated checks must not be affected.
    problem = Problem()
    problem.addVariables(["a", "b"], [1, 2, 3])
    problem.addConstraint(InSetConstraint([1]), ["a"], label="a-in-1")
    problem.addConstraint(InSetConstraint([3]), ["a"], label="a-in-3")
    problem.addConstraint(lambda b: b == 1, ["b"], label="b-is-1")
    result = problem.findMinimalUnsatisfiableSubset()
    assert result.status == MusResult.UNSATISFIABLE
    assert set(result.conflict) == {"a-in-1", "a-in-3"}
    # The problem definition keeps its original domains.
    assert sorted(problem._variables["a"]) == [1, 2, 3]
    assert sorted(problem._variables["b"]) == [1, 2, 3]
    # Repeated solving of the very same problem stays consistent.
    assert problem.getSolutions() == []
    problem2 = Problem()
    problem2.addVariable("a", [1, 2, 3])
    problem2.addConstraint(InSetConstraint([1, 2]), ["a"])
    first = problem2.getSolutions()
    second = problem2.getSolutions()
    assert first == second
    assert len(first) == 2


def test_reset_clears_labels():
    problem = Problem()
    problem.addVariable("a", [1, 2])
    problem.addConstraint(lambda a: a == 1, ["a"], label="gone")
    problem.reset()
    problem.addVariable("a", [1, 2])
    problem.addConstraint(lambda a: a == 1, ["a"], label="gone")
    result = problem.findMinimalUnsatisfiableSubset()
    assert result.status == MusResult.SATISFIABLE


def test_fresh_domain_copies_are_used():
    problem = Problem()
    problem.addVariable("a", Domain([1, 2]))
    problem.addConstraint(lambda a: a == 1, ["a"], label="keep")
    problem.findMinimalUnsatisfiableSubset()
    assert isinstance(problem._variables["a"], Domain)
    assert list(problem._variables["a"]) == [1, 2]
