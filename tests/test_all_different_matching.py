import itertools

from constraint import (
    AllDifferentConstraint,
    AllDifferentMatchingConstraint,
    BacktrackingSolver,
    Problem,
    RecursiveBacktrackingSolver,
)


def brute_force_solutions(variables, domains):
    expected = []
    for values in itertools.product(*(domains[v] for v in variables)):
        if len(set(values)) == len(values):
            expected.append(dict(zip(variables, values)))
    return expected


def normalized(solutions):
    return sorted(sorted(solution.items()) for solution in solutions)


def solve_with(constraint, variables, domains, solver=None):
    problem = Problem(solver) if solver else Problem()
    for variable in variables:
        problem.addVariable(variable, domains[variable])
    problem.addConstraint(constraint, variables)
    return problem.getSolutions()


CASES = [
    (["a", "b"], {"a": [1, 2], "b": [1, 2]}),
    (["a", "b", "c"], {"a": [1, 2, 3], "b": [1, 2, 3], "c": [1, 2, 3]}),
    (
        ["a", "b", "c", "d"],
        {"a": [1, 2], "b": [1, 2], "c": [1, 2, 3], "d": [3, 4]},
    ),
    (
        ["a", "b", "c"],
        {"a": [1, 2], "b": [2, 3], "c": [1, 3]},
    ),
    (
        ["a", "b", "c", "d"],
        {"a": [1, 2, 3], "b": [2, 3, 4], "c": [1, 3, 4], "d": [1, 2, 4]},
    ),
    # Hall violation: three variables, only two distinct values.
    (["a", "b", "c"], {"a": [1, 2], "b": [1, 2], "c": [1, 2]}),
]


def test_solutions_match_brute_force_enumeration():
    for variables, domains in CASES:
        expected = normalized(brute_force_solutions(variables, domains))
        solutions = solve_with(
            AllDifferentMatchingConstraint(), variables, domains
        )
        assert normalized(solutions) == expected


def test_solutions_match_lightweight_constraint():
    for variables, domains in CASES:
        expected = solve_with(AllDifferentConstraint(), variables, domains)
        for solver in (None, RecursiveBacktrackingSolver()):
            solutions = solve_with(
                AllDifferentMatchingConstraint(), variables, domains, solver
            )
            assert normalized(solutions) == normalized(expected)


def test_scheduling_hall_violation_detected_before_branching():
    # Three shifts must be staffed, but only two people are available.
    variables = ["shift1", "shift2", "shift3"]
    domains = dict((variable, ["ann", "bob"]) for variable in variables)

    problem = Problem()
    for variable in variables:
        problem.addVariable(variable, domains[variable])
    problem.addConstraint(AllDifferentMatchingConstraint(), variables)

    # The contradiction shows up while preprocessing, before any search.
    assert problem._getArgs() == (None, None, None)
    assert problem.getSolution() is None
    assert problem.getSolutions() == []

    # The lightweight constraint only fails later, during the search.
    light = Problem()
    for variable in variables:
        light.addVariable(variable, domains[variable])
    light.addConstraint(AllDifferentConstraint(), variables)
    domains_args, _, _ = light._getArgs()
    assert all(domains_args[v] == ["ann", "bob"] for v in variables)
    assert light.getSolutions() == []


def test_hall_set_prunes_domains_before_first_branch():
    # {a, b} form a Hall set over {1, 2}, so c and d cannot use 1 or 2,
    # and d cannot use 3 either once c is restricted to {3}.
    problem = Problem()
    problem.addVariable("a", [1, 2])
    problem.addVariable("b", [1, 2])
    problem.addVariable("c", [1, 2, 3])
    problem.addVariable("d", [3, 4])
    problem.addConstraint(
        AllDifferentMatchingConstraint(), ["a", "b", "c", "d"]
    )

    domains, _, _ = problem._getArgs()
    assert list(domains["a"]) == [1, 2]
    assert list(domains["b"]) == [1, 2]
    assert list(domains["c"]) == [3]
    assert list(domains["d"]) == [4]

    expected = [
        {"a": 1, "b": 2, "c": 3, "d": 4},
        {"a": 2, "b": 1, "c": 3, "d": 4},
    ]
    assert normalized(problem.getSolutions()) == normalized(expected)


def test_values_used_by_other_matchings_are_kept():
    # The matching found first cannot use every edge; values that only
    # appear in some other maximum matching must not be removed.
    problem = Problem()
    problem.addVariable("a", [1, 2])
    problem.addVariable("b", [1, 2])
    problem.addConstraint(AllDifferentMatchingConstraint(), ["a", "b"])

    domains, _, _ = problem._getArgs()
    assert list(domains["a"]) == [1, 2]
    assert list(domains["b"]) == [1, 2]

    expected = [{"a": 1, "b": 2}, {"a": 2, "b": 1}]
    assert normalized(problem.getSolutions()) == normalized(expected)


def test_domain_changes_are_undone_when_backtracking():
    # Solving repeatedly must give the same answer: values hidden while
    # propagating one branch are restored before sibling branches run.
    variables = ["a", "b", "c"]
    domains = {"a": [1, 2, 3], "b": [1, 2, 3], "c": [1, 2, 3]}
    problem = Problem(BacktrackingSolver())
    for variable in variables:
        problem.addVariable(variable, domains[variable])
    problem.addConstraint(AllDifferentMatchingConstraint(), variables)

    first = problem.getSolutions()
    second = problem.getSolutions()
    assert len(first) == 6
    assert normalized(first) == normalized(second)
    assert normalized(first) == normalized(
        brute_force_solutions(variables, domains)
    )
