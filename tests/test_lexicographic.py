from constraint import (
    Domain,
    LinearExpression,
    LexicographicResult,
    MinConflictsSolver,
    Problem,
)
import pytest


def make_scheduling_problem():
    # Two employees pick overtime x, y in {0, 1, 2} hours.  The workload
    # requires at least 2 hours of overtime.  Objectives:
    #   1. minimize total overtime         x + y
    #   2. among ties, give the overtime
    #      to the cheaper employee x       -x
    problem = Problem()
    problem.addVariables(["x", "y"], [0, 1, 2])
    problem.addConstraint(lambda x, y: x + y >= 2, ["x", "y"])
    return problem


def test_lexicographic_order_hand_checked_one():
    # Feasible (x, y): (0,2), (1,1), (1,2), (2,0), (2,1), (2,2).
    # Objective 1 (x+y): 2 for (0,2),(1,1),(2,0).
    # Objective 2 (-x)  : among those, (2,0) with -2 is minimal.
    problem = make_scheduling_problem()
    result = problem.getSolutionLexicographic(
        [LinearExpression({"x": 1, "y": 1}), LinearExpression({"x": -1})]
    )
    assert result.status == LexicographicResult.OPTIMAL
    assert result.proven_optimal is True
    assert result.budget_exhausted is False
    assert result.solution == {"x": 2, "y": 0}
    assert result.objective_values == (2, -2)
    assert result.solutions == ({"x": 2, "y": 0},)
    assert bool(result) is True


def test_lexicographic_order_hand_checked_all():
    problem = make_scheduling_problem()
    result = problem.getSolutionLexicographic(
        [{"x": 1, "y": 1}, ({"x": -1}, 0)], mode="all"
    )
    assert result.status == LexicographicResult.OPTIMAL
    assert result.objective_values == (2, -2)
    assert result.solutions == ({"x": 2, "y": 0},)


def test_second_objective_only_matters_on_ties():
    # Without the second objective all three overtime-2 schedules are best.
    problem = make_scheduling_problem()
    result = problem.getSolutionLexicographic(
        [LinearExpression({"x": 1, "y": 1})], mode="all"
    )
    assert result.status == LexicographicResult.OPTIMAL
    assert result.objective_values == (2,)
    key = lambda solution: tuple(sorted(solution.items()))
    assert sorted(result.solutions, key=key) == sorted(
        ({"x": 0, "y": 2}, {"x": 1, "y": 1}, {"x": 2, "y": 0}), key=key
    )

    # With the opposite tie breaker (-y) a different one is picked.
    problem = make_scheduling_problem()
    result = problem.getSolutionLexicographic(
        [LinearExpression({"x": 1, "y": 1}), LinearExpression({"y": -1})]
    )
    assert result.solution == {"x": 0, "y": 2}
    assert result.objective_values == (2, -2)


def test_negative_coefficients_and_constant():
    # Minimize -a + 2b - 3 over a, b in {-2, -1, 0, 1}.
    # Best: a = 1, b = -2  ->  -1 - 4 - 3 = -8.
    problem = Problem()
    problem.addVariables("ab", [-2, -1, 0, 1])
    result = problem.getSolutionLexicographic(
        [LinearExpression({"a": -1, "b": 2}, constant=-3)]
    )
    assert result.status == LexicographicResult.OPTIMAL
    assert result.solution == {"a": 1, "b": -2}
    assert result.objective_values == (-8,)


def test_constant_only_shifts_values():
    problem = Problem()
    problem.addVariable("a", [1, 2, 3])
    result = problem.getSolutionLexicographic([LinearExpression({}, constant=10)])
    assert result.solution == {"a": 1}
    assert result.objective_values == (10,)


def test_lower_bound_with_negative_coefficients():
    expression = LinearExpression({"a": 1, "b": -2}, constant=4)
    domains = {"a": Domain([1, 5]), "b": Domain([-3, 2])}
    # constant + 1*min(a) + (-2)*max(b) = 4 + 1 - 4 = 1
    assert expression.lowerBound(domains, {}) == 1
    # With a assigned 3: 4 + 3 + (-2)*max(b) = 4 + 3 - 4 = 3
    assert expression.lowerBound(domains, {"a": 3}) == 3
    # Fully assigned is exact: 4 + 5 + 6 = 15
    assert expression.evaluate({"a": 5, "b": -3}) == 15


def test_infeasible_is_distinct_from_exhausted():
    problem = Problem()
    problem.addVariable("z", [1, 2])
    problem.addConstraint(lambda z: z > 3, ["z"])
    result = problem.getSolutionLexicographic([LinearExpression({"z": 1})])
    assert result.status == LexicographicResult.INFEASIBLE
    assert result.proven_optimal is False
    assert result.budget_exhausted is False
    assert result.solution is None
    assert result.solutions == ()
    assert result.objective_values is None
    assert bool(result) is False


def test_empty_problem_is_infeasible():
    result = Problem().getSolutionLexicographic([LinearExpression({}, constant=0)])
    assert result.status == LexicographicResult.INFEASIBLE


def test_works_with_any_configured_solver():
    # MinConflictsSolver does not expose a "_forwardcheck" attribute; the
    # lexicographic entry must still work and use its own backtracking search.
    problem = Problem(MinConflictsSolver(steps=10))
    problem.addVariable("z", [1, 2])
    feasible = problem.getSolutionLexicographic([LinearExpression({"z": 1})])
    assert feasible.status == LexicographicResult.OPTIMAL
    assert feasible.solution == {"z": 1}

    problem.addConstraint(lambda z: z > 3, ["z"])
    infeasible = problem.getSolutionLexicographic([LinearExpression({"z": 1})])
    assert infeasible.status == LexicographicResult.INFEASIBLE


def test_budget_exhausted_without_incumbent():
    problem = Problem()
    problem.addVariables("abc", range(4))
    result = problem.getSolutionLexicographic(
        [LinearExpression({"a": 1, "b": 1, "c": 1})], node_budget=1
    )
    assert result.status == LexicographicResult.EXHAUSTED
    assert result.proven_optimal is False
    assert result.budget_exhausted is True
    assert result.solution is None
    assert result.solutions == ()
    assert result.nodes_visited == 1


def test_budget_exhausted_keeps_incumbent_but_unproven():
    problem = Problem()
    problem.addVariables("abc", range(4))
    result = problem.getSolutionLexicographic(
        [LinearExpression({"a": 1, "b": 1, "c": 1})], node_budget=5
    )
    assert result.status == LexicographicResult.EXHAUSTED
    assert result.proven_optimal is False
    assert result.budget_exhausted is True
    assert result.solution == {"a": 0, "b": 0, "c": 0}
    assert result.objective_values == (0,)
    assert result.nodes_visited <= 5


def test_budget_large_enough_proves_optimal():
    problem = Problem()
    problem.addVariables("abc", range(4))
    full = problem.getSolutionLexicographic(
        [LinearExpression({"a": 1, "b": 1, "c": 1})]
    )
    budgeted = problem.getSolutionLexicographic(
        [LinearExpression({"a": 1, "b": 1, "c": 1})],
        node_budget=full.nodes_visited,
    )
    assert budgeted.status == LexicographicResult.OPTIMAL
    assert budgeted.solution == {"a": 0, "b": 0, "c": 0}
    assert budgeted.nodes_visited == full.nodes_visited


def test_pruning_reduces_nodes():
    # The objective only involves a and b; c is free.  Feasible branches
    # have bound == best at the leaves only, so pruning can only skip
    # branches whose lower bound is strictly above the optimum.
    def solve(pruning, mode):
        problem = Problem()
        problem.addVariables("abc", range(5))
        problem.addConstraint(lambda a, b: a + b <= 2, ["a", "b"])
        return problem.getSolutionLexicographic(
            [LinearExpression({"a": 1, "b": 1})],
            mode=mode,
            pruning=pruning,
        )

    for mode, expected_count in (("one", 1), ("all", 5)):
        unpruned = solve(False, mode)
        pruned = solve(True, mode)
        assert unpruned.objective_values == pruned.objective_values == (0,)
        assert len(pruned.solutions) == expected_count
        assert pruned.nodes_visited < unpruned.nodes_visited
        assert unpruned.nodes_visited == 40
        assert pruned.nodes_visited == 12

    # Tied optima in "all" mode: a = b = 0, c free in {0..4}.
    result = solve(True, "all")
    key = lambda solution: tuple(sorted(solution.items()))
    assert sorted(result.solutions, key=key) == sorted(
        (
            {"a": 0, "b": 0, "c": 0},
            {"a": 0, "b": 0, "c": 1},
            {"a": 0, "b": 0, "c": 2},
            {"a": 0, "b": 0, "c": 3},
            {"a": 0, "b": 0, "c": 4},
        ),
        key=key,
    )


def test_pruning_disabled_still_finds_optimum():
    problem = make_scheduling_problem()
    result = problem.getSolutionLexicographic(
        [LinearExpression({"x": 1, "y": 1}), LinearExpression({"x": -1})],
        pruning=False,
    )
    assert result.status == LexicographicResult.OPTIMAL
    assert result.solution == {"x": 2, "y": 0}


def test_forwardchecking_also_bounds_pruning():
    def solve(forwardcheck):
        problem = Problem(Problem().getSolver().__class__(forwardcheck))
        problem.addVariables("abc", range(4))
        problem.addConstraint(lambda a, b: a + b == 3, ["a", "b"])
        problem.addConstraint(lambda b, c: b > c, ["b", "c"])
        result = problem.getSolutionLexicographic(
            [LinearExpression({"a": 1, "b": 1, "c": 1})]
        )
        return result

    with_forwardcheck = solve(True)
    without_forwardcheck = solve(False)
    assert with_forwardcheck.solution == without_forwardcheck.solution
    assert with_forwardcheck.objective_values == (3,)


def test_plain_getsolutions_semantics_unchanged():
    problem = make_scheduling_problem()
    solutions = problem.getSolutions()
    assert isinstance(solutions, list)
    assert len(solutions) == 6
    assert problem.getSolution() in solutions


def test_invalid_objective_and_arguments():
    problem = Problem()
    problem.addVariable("a", [1, 2])
    with pytest.raises(ValueError):
        problem.getSolutionLexicographic([])
    with pytest.raises(ValueError):
        problem.getSolutionLexicographic([LinearExpression({"unknown": 1})])
    with pytest.raises(ValueError):
        problem.getSolutionLexicographic([LinearExpression({"a": 0.5})])
    with pytest.raises(ValueError):
        problem.getSolutionLexicographic([LinearExpression({}, constant="x")])
    with pytest.raises(ValueError):
        problem.getSolutionLexicographic(
            [LinearExpression({"a": 1})], mode="everything"
        )
    with pytest.raises(ValueError):
        problem.getSolutionLexicographic(
            [LinearExpression({"a": 1})], node_budget=0
        )
    with pytest.raises(ValueError):
        problem.getSolutionLexicographic([object()])
