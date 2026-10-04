import itertools

from constraint import (
    AllDifferentConstraint,
    AllEqualConstraint,
    Domain,
    ExactSumConstraint,
    FunctionConstraint,
    MaxSumConstraint,
    MinSumConstraint,
    Problem,
    RecursiveBacktrackingSolver,
    ReifiedConstraint,
    Unassigned,
)


def brute_force(domains, predicate):
    variables = list(domains)
    solutions = set()
    for values in itertools.product(*(domains[v] for v in variables)):
        assignment = dict(zip(variables, values))
        if predicate(assignment):
            solutions.add(tuple(sorted(assignment.items())))
    return solutions


def solution_set(problem):
    return set(tuple(sorted(s.items())) for s in problem.getSolutions())


def build_discount_problem(flag_domain=(False, True), solver=None):
    problem = Problem(solver)
    problem.addVariables(["small", "large"], range(5))
    problem.addVariable("discount", list(flag_domain))
    # The discount applies exactly when the order totals at least 5 units.
    problem.addReifiedConstraint(MinSumConstraint(5), "discount", ["small", "large"])
    # Discounted orders must include at least one large item.
    problem.addConstraint(
        lambda small, large, discount: not discount or large >= 1,
        ["small", "large", "discount"],
    )
    return problem


def discount_rule(assignment):
    holds = assignment["small"] + assignment["large"] >= 5
    if assignment["discount"] != holds:
        return False
    return not assignment["discount"] or assignment["large"] >= 1


def test_conditional_discount_matches_brute_force():
    problem = build_discount_problem()
    expected = brute_force(
        {"small": range(5), "large": range(5), "discount": (False, True)},
        discount_rule,
    )
    assert solution_set(problem) == expected


def test_conditional_discount_recursive_solver():
    problem = build_discount_problem(solver=RecursiveBacktrackingSolver())
    expected = brute_force(
        {"small": range(5), "large": range(5), "discount": (False, True)},
        discount_rule,
    )
    assert solution_set(problem) == expected


def test_exactly_one_rule_matches_brute_force():
    problem = Problem()
    problem.addVariables(["x", "y"], range(5))
    problem.addVariables(["bulk", "mixed"], [False, True])
    problem.addReifiedConstraint(MinSumConstraint(5), "bulk", ["x", "y"])
    problem.addReifiedConstraint(AllDifferentConstraint(), "mixed", ["x", "y"])
    # Exactly one of the two rules is allowed to hold.
    problem.addConstraint(ExactSumConstraint(1), ["bulk", "mixed"])

    def rule(assignment):
        holds1 = assignment["x"] + assignment["y"] >= 5
        holds2 = assignment["x"] != assignment["y"]
        return (
            assignment["bulk"] == holds1
            and assignment["mixed"] == holds2
            and holds1 + holds2 == 1
        )

    expected = brute_force(
        {"x": range(5), "y": range(5), "bulk": (False, True), "mixed": (False, True)},
        rule,
    )
    assert solution_set(problem) == expected


def test_fixed_flag_branches_prune_differently():
    constraint = ReifiedConstraint(ExactSumConstraint(5))
    variables = ["x", "y", "flag"]

    domains = {"x": Domain([1, 2, 3]), "y": Domain([2, 3, 4]), "flag": Domain([True])}
    assert constraint(variables, domains, {"x": 1, "flag": True}, True)
    assert list(domains["y"]) == [4]

    domains = {"x": Domain([1, 2, 3]), "y": Domain([2, 3, 4]), "flag": Domain([False])}
    assert constraint(variables, domains, {"x": 1, "flag": False}, True)
    assert list(domains["y"]) == [2, 3]


def test_fixed_flag_branches_yield_different_domains():
    def projections(flag_domain):
        problem = Problem()
        problem.addVariables(["x", "y"], [1, 2, 3, 4])
        problem.addVariable("flag", list(flag_domain))
        problem.addReifiedConstraint(ExactSumConstraint(5), "flag", ["x", "y"])
        return set((s["x"], s["y"]) for s in problem.getSolutions())

    both = projections((False, True))
    only_true = projections((True,))
    only_false = projections((False,))
    assert only_true == set((x, y) for (x, y) in both if x + y == 5)
    assert only_false == set((x, y) for (x, y) in both if x + y != 5)
    assert only_true and only_false
    assert only_true != only_false
    assert only_true | only_false == both


def test_negation_is_whole_relation_not_itemwise():
    # flag=False with AllDifferent means "some pair is equal".
    # Negating item by item would wrongly require all values equal.
    problem = Problem()
    problem.addVariables(["x", "y", "z"], [1, 2])
    problem.addVariable("flag", [False])
    problem.addReifiedConstraint(AllDifferentConstraint(), "flag", ["x", "y", "z"])
    solutions = problem.getSolutions()
    assert len(solutions) == 8
    assert all(len(set((s["x"], s["y"], s["z"]))) < 3 for s in solutions)
    assert any(len(set((s["x"], s["y"], s["z"]))) == 2 for s in solutions)


def test_negation_of_all_equal():
    problem = Problem()
    problem.addVariables(["x", "y"], [1, 2])
    problem.addVariable("flag", [False])
    problem.addReifiedConstraint(AllEqualConstraint(), "flag", ["x", "y"])
    solutions = problem.getSolutions()
    assert len(solutions) == 2
    assert all(s["x"] != s["y"] for s in solutions)


def test_user_function_never_receives_unassigned():
    calls = []

    def func(x, y):
        calls.append((x, y))
        return x * 2 == y

    problem = Problem()
    problem.addVariables(["x", "y"], [1, 2, 3])
    problem.addVariable("flag", [False, True])
    problem.addReifiedConstraint(FunctionConstraint(func), "flag", ["x", "y"])
    solutions = problem.getSolutions()
    assert calls
    assert all(Unassigned not in call for call in calls)
    expected = brute_force(
        {"x": [1, 2, 3], "y": [1, 2, 3], "flag": (False, True)},
        lambda a: a["flag"] == (a["x"] * 2 == a["y"]),
    )
    assert set(tuple(sorted(s.items())) for s in solutions) == expected


def test_undecided_partial_assignment_keeps_both_values():
    constraint = ReifiedConstraint(ExactSumConstraint(5))
    variables = ["x", "y", "flag"]
    domains = {
        "x": Domain([1, 2]),
        "y": Domain([2, 3, 4]),
        "flag": Domain([False, True]),
    }
    # x=1 leaves the outcome undecided (y=4 satisfies, y=2 doesn't).
    assert constraint(variables, domains, {"x": 1}, True)
    assert list(domains["flag"]) == [False, True]
    assert list(domains["y"]) == [2, 3, 4]


def test_decided_partial_assignment_prunes_flag():
    constraint = ReifiedConstraint(MinSumConstraint(5))
    variables = ["x", "y", "flag"]
    domains = {
        "x": Domain([1]),
        "y": Domain([1, 2]),
        "flag": Domain([False, True]),
    }
    # x=1 and y<=2 can never reach a sum of 5, so flag must be false.
    assert constraint(variables, domains, {"x": 1}, True)
    assert list(domains["flag"]) == [False]


def test_broken_partial_assignment_forces_false():
    constraint = ReifiedConstraint(MaxSumConstraint(3))
    variables = ["x", "y", "z", "flag"]
    domains = {
        "x": Domain([5]),
        "y": Domain([1]),
        "z": Domain([1]),
        "flag": Domain([False, True]),
    }
    # x=5 alone already exceeds the maximum sum.
    assert constraint(variables, domains, {"x": 5}, True)
    assert list(domains["flag"]) == [False]
