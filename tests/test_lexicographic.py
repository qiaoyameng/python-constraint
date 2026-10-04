from itertools import product

import pytest

from constraint import (
    Domain,
    LinearExpr,
    OptimizationResult,
    Problem,
)


def brute_force_optima(problem, objectives):
    """Return (objective_tuple, all_solutions_achieving_it) by enumeration."""
    best = None
    winners = []
    for solution in problem.getSolutions():
        values = tuple(expr.value(solution) for expr in objectives)
        if best is None or values < best:
            best = values
            winners = [solution]
        elif values == best:
            winners.append(solution)
    return best, winners


def normalize(solutions):
    return sorted((tuple(sorted(solution.items())) for solution in solutions))


# ---------------------------------------------------------------------------
# LinearExpr
# ---------------------------------------------------------------------------


def test_linear_expr_value_with_negative_and_constant():
    expr = LinearExpr({"a": 1, "b": -2}, constant=5)
    assert expr.value({"a": 3, "b": 4}) == 3 - 8 + 5
    assert expr.constant == 5
    assert expr.coefficients == {"a": 1, "b": -2}


def test_linear_expr_lower_bound_uses_domain_extrema():
    expr = LinearExpr({"a": 1, "b": -1}, constant=10)
    domains = {"a": Domain([1, 2, 3]), "b": Domain([1, 2, 3])}
    # min of +1*a is 1, min of -1*b is -max(b) = -3
    assert expr.lower_bound({}, domains) == 1 - 3 + 10
    # assigned variables contribute their assigned value
    assert expr.lower_bound({"a": 3}, domains) == 3 - 3 + 10


def test_linear_expr_rejects_non_integer_terms():
    with pytest.raises(ValueError):
        LinearExpr({"a": 1.5})
    with pytest.raises(ValueError):
        LinearExpr(constant=1.0)
    with pytest.raises(ValueError):
        LinearExpr({"a": True})


# ---------------------------------------------------------------------------
# Lexicographic ordering on hand-computed examples
# ---------------------------------------------------------------------------


def test_hand_computed_lexicographic_order():
    # x,y in 1..3, x != y; minimize f1 = x - y, then f2 = x + y + 10.
    # Enumeration shows f1 can be -2 only with (x, y) = (1, 3), f2 = 14.
    # A low cost cannot rescue a worse overtime value: (3, 1) has f1 = 2.
    problem = Problem()
    problem.addVariables(["x", "y"], [1, 2, 3])
    problem.addConstraint(lambda x, y: x != y, ["x", "y"])
    overtime = LinearExpr({"x": 1, "y": -1})
    cost = LinearExpr({"x": 1, "y": 1}, constant=10)

    result = problem.minimizeLexicographic([overtime, cost])

    assert result.status == OptimizationResult.OPTIMAL
    assert result.is_optimal
    assert result.solution == {"x": 1, "y": 3}
    assert result.objective_values == [-2, 14]


def test_scheduling_story_minimize_overtime_then_balance_cost():
    # Two workers may take 0..2 overtime hours; at least one hour must be
    # covered. Overtime hours are minimized first; among equal overtime the
    # (negated) subsidy is minimized, preferring the worker paid 20.
    problem = Problem()
    problem.addVariables(["o1", "o2"], [0, 1, 2])
    problem.addConstraint(lambda o1, o2: o1 + o2 >= 1, ["o1", "o2"])
    overtime = LinearExpr({"o1": 1, "o2": 1})
    subsidy = LinearExpr({"o1": -10, "o2": -20})

    single = problem.minimizeLexicographic([overtime, subsidy])
    assert single.solution == {"o1": 0, "o2": 1}
    assert single.objective_values == [1, -20]

    every = problem.minimizeLexicographic(
        [overtime, subsidy], all_solutions=True
    )
    assert normalize(every.solutions) == normalize([{"o1": 0, "o2": 1}])


def test_second_objective_only_breaks_ties():
    # Minimize x; among ties maximize y via -y.
    problem = Problem()
    problem.addVariables(["x", "y"], [0, 1, 2])
    result = problem.minimizeLexicographic(
        [LinearExpr({"x": 1}), LinearExpr({"y": -1})]
    )
    assert result.solution == {"x": 0, "y": 2}
    assert result.objective_values == [0, -2]


def test_constant_term_shifts_values_not_choices():
    problem = Problem()
    problem.addVariables(["x"], [1, 2, 3])
    result = problem.minimizeLexicographic([LinearExpr({"x": 1}, 100)])
    assert result.solution == {"x": 1}
    assert result.objective_values == [101]


def test_all_optimal_solutions_are_returned_for_ties():
    problem = Problem()
    problem.addVariables(["x", "y"], [0, 1])
    result = problem.minimizeLexicographic(
        [LinearExpr({"x": 1})], all_solutions=True
    )
    assert result.status == OptimizationResult.OPTIMAL
    assert normalize(result.solutions) == normalize(
        [{"x": 0, "y": 0}, {"x": 0, "y": 1}]
    )
    assert result.objective_values == [0]


def test_single_solution_mode_returns_one_optimum():
    problem = Problem()
    problem.addVariables(["x", "y"], [0, 1])
    result = problem.minimizeLexicographic([LinearExpr({"x": 1})])
    assert result.solution in ({"x": 0, "y": 0}, {"x": 0, "y": 1})
    assert result.solutions is None


def test_dict_objectives_are_accepted():
    problem = Problem()
    problem.addVariables(["x", "y"], [1, 2])
    result = problem.minimizeLexicographic([{"x": 1}, {"y": -1}])
    assert result.solution == {"x": 1, "y": 2}
    assert result.objective_values == [1, -2]


@pytest.mark.parametrize("forwardcheck", [True, False])
def test_matches_brute_force_on_random_small_problems(forwardcheck):
    import random

    rng = random.Random(1234)
    for _ in range(30):
        problem = Problem()
        names = ["v0", "v1", "v2"]
        for name in names:
            problem.addVariable(name, [0, 1, 2])
        if rng.random() < 0.5:
            left, right = rng.sample(names, 2)
            problem.addConstraint(
                lambda a, b: a != b, [left, right]
            )
        objectives = [
            LinearExpr(
                {name: rng.randint(-2, 2) for name in names},
                constant=rng.randint(-3, 3),
            )
            for _ in range(rng.randint(1, 3))
        ]

        best, winners = brute_force_optima(problem, objectives)

        single = problem.minimizeLexicographic(
            objectives, forwardcheck=forwardcheck
        )
        assert single.status == OptimizationResult.OPTIMAL
        assert tuple(single.objective_values) == best
        assert single.solution in winners

        every = problem.minimizeLexicographic(
            objectives, all_solutions=True, forwardcheck=forwardcheck
        )
        assert tuple(every.objective_values) == best
        assert normalize(every.solutions) == normalize(winners)


# ---------------------------------------------------------------------------
# Infeasibility
# ---------------------------------------------------------------------------


def test_infeasible_problem_is_distinct_from_budget_and_optimal():
    problem = Problem()
    problem.addVariable("x", [0, 1])
    problem.addConstraint(lambda x: x > 5, ["x"])
    result = problem.minimizeLexicographic([LinearExpr({"x": 1})])

    assert result.status == OptimizationResult.INFEASIBLE
    assert result.is_infeasible
    assert not result.is_optimal
    assert not result.is_budget_exhausted
    assert result.solution is None
    assert result.solutions is None
    assert result.objective_values is None


def test_problem_without_variables_is_infeasible():
    result = Problem().minimizeLexicographic([LinearExpr({})])
    assert result.status == OptimizationResult.INFEASIBLE


# ---------------------------------------------------------------------------
# Node budget
# ---------------------------------------------------------------------------


def test_budget_exhausted_keeps_incumbent_without_claiming_optimality():
    # Full search for two unconstrained 1..3 variables visits 13 nodes
    # (root, 3 children, 9 leaves). A budget of 4 finds (1, 1) but cannot
    # prove it optimal.
    problem = Problem()
    problem.addVariables(["x", "y"], [1, 2, 3])

    result = problem.minimizeLexicographic(
        [LinearExpr({"x": 1}), LinearExpr({"y": 1})], node_budget=4
    )

    assert result.status == OptimizationResult.BUDGET_EXHAUSTED
    assert result.is_budget_exhausted
    assert not result.is_optimal
    assert result.solution == {"x": 1, "y": 1}
    assert result.objective_values == [1, 1]
    assert result.nodes == 5


def test_budget_smaller_than_first_solution_has_no_incumbent():
    problem = Problem()
    problem.addVariables(["x", "y"], [1, 2, 3])
    result = problem.minimizeLexicographic(
        [LinearExpr({"x": 1})], node_budget=1
    )
    # Not infeasible: the search simply was not allowed to finish.
    assert result.status == OptimizationResult.BUDGET_EXHAUSTED
    assert result.solution is None
    assert result.is_infeasible is False


def test_budget_large_enough_proves_optimality():
    problem = Problem()
    problem.addVariables(["x", "y"], [0, 1])
    result = problem.minimizeLexicographic(
        [LinearExpr({"x": 1}), LinearExpr({"y": 1})], node_budget=7
    )
    assert result.status == OptimizationResult.OPTIMAL
    assert result.solution == {"x": 0, "y": 0}


def test_budget_exhausted_all_solutions_returns_incumbents_found():
    problem = Problem()
    problem.addVariables(["x", "y"], [0, 1, 2])
    result = problem.minimizeLexicographic(
        [LinearExpr({"x": 1})], all_solutions=True, node_budget=6
    )
    assert result.status == OptimizationResult.BUDGET_EXHAUSTED
    assert not result.is_optimal
    assert normalize(result.solutions) == normalize(
        [{"x": 0, "y": 0}, {"x": 0, "y": 1}, {"x": 0, "y": 2}]
    )


def test_invalid_budget_is_rejected():
    problem = Problem()
    problem.addVariable("x", [0, 1])
    for bad in (0, -1, 1.5, "10", True):
        with pytest.raises(ValueError):
            problem.minimizeLexicographic(
                [LinearExpr({"x": 1})], node_budget=bad
            )


# ---------------------------------------------------------------------------
# Pruning
# ---------------------------------------------------------------------------


def test_pruning_reduces_node_count_without_changing_result():
    problem = Problem()
    problem.addVariables(["x", "y"], [1, 2, 3])
    objectives = [LinearExpr({"x": 1}), LinearExpr({"y": 1})]

    unpruned = problem.minimizeLexicographic(objectives, prune=False)
    pruned = problem.minimizeLexicographic(objectives, prune=True)

    # Without pruning the complete 1 + 3 + 9 tree is walked.
    assert unpruned.nodes == 13
    # Pruning skips subtrees once the incumbent (1, 1) is found.
    assert pruned.nodes == 7
    assert pruned.nodes < unpruned.nodes
    assert pruned.solution == unpruned.solution == {"x": 1, "y": 1}


def test_pruning_cutoff_for_all_optimal_mode_keeps_ties():
    problem = Problem()
    problem.addVariables(["x", "y"], [0, 1])
    result = problem.minimizeLexicographic(
        [LinearExpr({"x": 1})], all_solutions=True
    )
    assert len(result.solutions) == 2
    # Equal lower bounds are not pruned, strictly worse ones are.
    assert result.nodes < 7


def test_negative_coefficient_pruning_is_sound():
    # With a -x objective the optimum (x = 3) is reached late; pruning must
    # not use a naive "minimum domain value" lower bound.
    problem = Problem()
    problem.addVariables(["x", "y"], [1, 2, 3])
    result = problem.minimizeLexicographic(
        [LinearExpr({"x": -1}), LinearExpr({"y": 1})]
    )
    assert result.solution == {"x": 3, "y": 1}
    assert result.objective_values == [-3, 1]


# ---------------------------------------------------------------------------
# Validation and backwards compatibility
# ---------------------------------------------------------------------------


def test_objective_validation():
    problem = Problem()
    problem.addVariable("x", [0, 1])
    with pytest.raises(ValueError):
        problem.minimizeLexicographic([])
    with pytest.raises(TypeError):
        problem.minimizeLexicographic([42])
    with pytest.raises(TypeError):
        problem.minimizeLexicographic(LinearExpr({"x": 1}))


def test_plain_get_solutions_semantics_unchanged():
    problem = Problem()
    assert problem.getSolutions() == []
    assert problem.getSolution() is None
    problem.addVariables(["x", "y"], [1, 2, 3])
    problem.addConstraint(lambda x, y: y > x, ["x", "y"])
    assert len(problem.getSolutions()) == 3
    assert problem.getSolution() in problem.getSolutions()
