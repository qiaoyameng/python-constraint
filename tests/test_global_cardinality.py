from itertools import product

import pytest

from constraint import (
    Domain,
    Problem,
    BacktrackingSolver,
    RecursiveBacktrackingSolver,
    GlobalCardinalityConstraint,
    Variable,
)


def brute_force_solutions(names, domains, bounds, closed):
    bounds = dict(
        (key, (value, value) if isinstance(value, int) else value)
        for key, value in bounds.items()
    )
    values = [domains[name] for name in names]
    solutions = []
    for assignment in product(*values):
        counts = {}
        valid = True
        for value in assignment:
            if closed and value not in bounds:
                valid = False
                break
            counts[value] = counts.get(value, 0) + 1
        if not valid:
            continue
        for value, (minimum, maximum) in bounds.items():
            count = counts.get(value, 0)
            if count < minimum or count > maximum:
                valid = False
                break
        if valid:
            solutions.append(dict(zip(names, assignment)))
    return solutions


def solve(names, domains, bounds, closed, solver=None):
    problem = Problem(solver or BacktrackingSolver())
    for name in names:
        problem.addVariable(name, domains[name])
    problem.addConstraint(
        GlobalCardinalityConstraint(dict(bounds), closed=closed), names
    )
    return problem.getSolutions()


def normalize(solutions):
    return sorted(sorted(solution.items()) for solution in solutions)


SOLVERS = [
    BacktrackingSolver(),
    BacktrackingSolver(forwardcheck=False),
    RecursiveBacktrackingSolver(),
    RecursiveBacktrackingSolver(forwardcheck=False),
]


@pytest.mark.parametrize("solver", SOLVERS)
def test_closed_exhaustive_small(solver):
    names = ["a", "b", "c"]
    domains = {
        "a": [1, 2, 3],
        "b": [1, 2],
        "c": [2, 3],
    }
    cases = [
        {1: (1, 2), 2: (0, 2), 3: (0, 1)},
        {1: 1, 2: 1},
        {1: (2, 3), 2: (0, 1), 3: (0, 1)},
        {2: 3},
        {1: (0, 1), 3: (2, 2)},
    ]
    for bounds in cases:
        expected = brute_force_solutions(names, domains, bounds, True)
        found = solve(names, domains, bounds, True, solver)
        assert normalize(found) == normalize(expected), bounds


@pytest.mark.parametrize("solver", SOLVERS)
def test_open_exhaustive_small(solver):
    names = ["a", "b", "c", "d"]
    domains = {
        "a": [1, 2, 9],
        "b": [1, 9],
        "c": [1, 2],
        "d": [2, 9],
    }
    cases = [
        {1: (1, 2)},
        {1: (1, 1), 2: (1, 1)},
        {1: (0, 0)},
        {1: (4, 4)},
        {2: (2, 3)},
        {1: (1, 2), 2: (1, 2)},
    ]
    for bounds in cases:
        expected = brute_force_solutions(names, domains, bounds, False)
        found = solve(names, domains, bounds, False, solver)
        assert normalize(found) == normalize(expected), bounds


@pytest.mark.parametrize("solver", SOLVERS)
def test_open_unlisted_value_is_free(solver):
    problem = Problem(solver)
    problem.addVariables(["a", "b"], ["x", "y"])
    problem.addConstraint(GlobalCardinalityConstraint({"x": (0, 1)}))
    solutions = problem.getSolutions()
    assert normalize(solutions) == [
        [("a", "x"), ("b", "y")],
        [("a", "y"), ("b", "x")],
        [("a", "y"), ("b", "y")],
    ]


def test_roster_single_shifts_feasible_but_jointly_overcommitted():
    # Three candidates, two shifts. Day needs 2, night needs 3.
    # Only two people can work the day shift; the remaining candidate
    # pool is too small to staff the night shift. Each shift alone looks
    # satisfiable, but the two shifts cannot be staffed simultaneously.
    candidates = ["alice", "bob", "carol"]
    shift_domain = {
        "alice": ["day", "night"],
        "bob": ["day", "night"],
        "carol": ["night"],
    }
    bounds = {"day": (2, 2), "night": (3, 3)}

    assert brute_force_solutions(candidates, shift_domain, bounds, True) == []

    problem = Problem()
    for candidate in candidates:
        problem.addVariable(candidate, shift_domain[candidate])
    problem.addConstraint(GlobalCardinalityConstraint(bounds, closed=True))
    assert problem.getSolutions() == []

    # Sanity check: relaxing the night requirement makes it feasible.
    problem = Problem()
    for candidate in candidates:
        problem.addVariable(candidate, shift_domain[candidate])
    problem.addConstraint(
        GlobalCardinalityConstraint({"day": (2, 2), "night": (1, 3)}, closed=True)
    )
    solution = problem.getSolution()
    assert solution == {"alice": "day", "bob": "day", "carol": "night"}


def test_roster_realistic_bounds_exhaustive():
    names = ["p1", "p2", "p3", "p4", "p5"]
    domains = {
        "p1": ["day", "night"],
        "p2": ["day", "night"],
        "p3": ["day", "night", "rest"],
        "p4": ["night", "rest"],
        "p5": ["day", "rest"],
    }
    bounds = {"day": (2, 3), "night": (1, 2), "rest": (0, 2)}
    expected = brute_force_solutions(names, domains, bounds, False)
    found = solve(names, domains, bounds, False)
    assert normalize(found) == normalize(expected)
    assert len(expected) > 0


def test_exact_integer_shorthand():
    names = ["a", "b", "c"]
    domains = {name: [1, 2, 3] for name in names}
    bounds = {1: 2, 3: 1}
    expected = brute_force_solutions(names, domains, bounds, True)
    found = solve(names, domains, bounds, True)
    assert normalize(found) == normalize(expected)
    for solution in found:
        counts = {}
        for value in solution.values():
            counts[value] = counts.get(value, 0) + 1
        assert counts[1] == 2
        assert counts[3] == 1
        assert 2 not in counts


def test_zero_upper_bound_forbids_value():
    problem = Problem()
    problem.addVariables(["a", "b"], [1, 2])
    problem.addConstraint(
        GlobalCardinalityConstraint({1: (0, 0)}, closed=False)
    )
    assert problem.getSolutions() == [{"a": 2, "b": 2}]


@pytest.mark.parametrize(
    "bounds,message",
    [
        ({1: (2, 1)}, "greater than its maximum"),
        ({1: (-1, 2)}, "not be negative"),
        ({1: (1, -1)}, "not be negative"),
        ({1: "nope"}, "exact count or a"),
        ({1: (1, 2, 3)}, "exact count or a"),
        ({1: 1.5}, "exact count or a"),
    ],
)
def test_invalid_bounds_raise(bounds, message):
    with pytest.raises(ValueError) as excinfo:
        GlobalCardinalityConstraint(bounds)
    assert message in str(excinfo.value)


def test_bounds_must_be_mapping():
    with pytest.raises(TypeError):
        GlobalCardinalityConstraint([(1, 2)])


def test_duplicated_variables_raise():
    problem = Problem()
    problem.addVariables(["a", "b"], [1, 2])
    problem.addConstraint(
        GlobalCardinalityConstraint({1: 1}, closed=True), ["a", "a", "b"]
    )
    with pytest.raises(ValueError) as excinfo:
        problem.getSolutions()
    assert "duplicated" in str(excinfo.value)


def test_forced_assignment_over_upper_bound_raises():
    problem = Problem()
    problem.addVariable("a", [1])
    problem.addVariable("b", [1])
    problem.addConstraint(GlobalCardinalityConstraint({1: (0, 1)}, closed=True))
    with pytest.raises(ValueError) as excinfo:
        problem.getSolutions()
    assert "forced" in str(excinfo.value)


def test_assignment_over_upper_bound_returns_false():
    constraint = GlobalCardinalityConstraint({1: (0, 1)})
    variables = ["a", "b"]
    assert not constraint(variables, {}, {"a": 1, "b": 1})
    assert constraint(variables, {}, {"a": 1})
    assert constraint(variables, {}, {"a": 2, "b": 3})


def test_fully_assigned_checks_lower_bound():
    constraint = GlobalCardinalityConstraint({1: (2, 2)})
    variables = ["a", "b"]
    assert constraint(variables, {}, {"a": 1, "b": 1})
    assert not constraint(variables, {}, {"a": 1, "b": 2})


def test_forward_check_restores_hidden_values_on_backtrack():
    problem = Problem()
    problem.addVariable("a", [1, 2])
    problem.addVariable("b", [1, 2])
    problem.addConstraint(
        GlobalCardinalityConstraint({1: (2, 2)}, closed=True)
    )
    solutions = problem.getSolutions()
    assert solutions == [{"a": 1, "b": 1}]

    # Domains are rebuilt per solve, but solving a second time proves no
    # pruning leaked through Domain state restoration.
    assert problem.getSolutions() == [{"a": 1, "b": 1}]


def test_hide_value_state_restored_directly():
    # Two unassigned variables, one already-assigned 1 and a minimum of
    # two 1s: value 2 must be hidden from the unassigned domains.
    constraint = GlobalCardinalityConstraint({1: (3, 3), 2: (0, 0)}, closed=True)
    v0, v1, v2 = variables = [
        Variable("v0"),
        Variable("v1"),
        Variable("v2"),
    ]
    domains = {
        v0: Domain([1]),
        v1: Domain([1, 2]),
        v2: Domain([1, 2]),
    }
    for domain in domains.values():
        domain.pushState()
    assert constraint(variables, domains, {v0: 1}, forwardcheck=True)
    assert list(domains[v2]) == [1]
    assert list(domains[v1]) == [1]
    domains[v2].popState()
    domains[v1].popState()
    assert list(domains[v2]) == [1, 2]
    assert list(domains[v1]) == [1, 2]


def test_shared_values_pruning_is_not_per_value_remainder():
    # Every variable can take both values and each value must appear
    # twice; no value may be pruned despite each one having exactly two
    # supporters left.
    constraint = GlobalCardinalityConstraint({"d": (2, 2), "n": (2, 2)}, closed=True)
    variables = ["w", "x", "y", "z"]
    domains = dict((name, Domain(["d", "n"])) for name in variables)
    assert constraint(variables, domains, {}, forwardcheck=True)
    for name in variables:
        assert list(domains[name]) == ["d", "n"]


def test_constraint_without_explicit_variables():
    problem = Problem()
    problem.addVariables(["a", "b"], [1, 2])
    problem.addConstraint(GlobalCardinalityConstraint({1: 1, 2: 1}, closed=True))
    assert normalize(problem.getSolutions()) == normalize(
        [{"a": 1, "b": 2}, {"a": 2, "b": 1}]
    )


def test_hall_infeasibility_shared_pool():
    # Both "a" and "b" need one variable and each alone has a supporter,
    # but the single variable able to take either of them cannot cover
    # both requirements at once. A per-value remainder check would not
    # see the conflict; the shared flow network does.
    problem = Problem()
    problem.addVariable("x", ["a", "b"])
    problem.addVariable("y", ["c"])
    problem.addConstraint(
        GlobalCardinalityConstraint({"a": 1, "b": 1, "c": (0, 1)}, closed=True)
    )
    assert problem.getSolutions() == []

    # Relaxing the requirement for "b" makes it feasible again.
    problem = Problem()
    problem.addVariable("x", ["a", "b"])
    problem.addVariable("y", ["c"])
    problem.addConstraint(
        GlobalCardinalityConstraint({"a": 1, "b": (0, 1), "c": (0, 1)}, closed=True)
    )
    assert normalize(problem.getSolutions()) == [[("x", "a"), ("y", "c")]]


def test_empty_variable_list_is_trivially_satisfied():
    problem = Problem()
    problem.addVariable("a", [1, 2])
    problem.addConstraint(GlobalCardinalityConstraint({3: (0, 0)}), [])
    assert normalize(problem.getSolutions()) == [[("a", 1)], [("a", 2)]]
