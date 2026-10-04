#!/usr/bin/env python
# -*- coding: utf-8 -*-

import constraint
from constraint import (
    AllDifferentConstraint,
    AllDifferentMatchingConstraint,
    BacktrackingSolver,
    Domain,
    Problem,
    RecursiveBacktrackingSolver,
)


def solve_all(variables_domains, constraint_factory, solver=None):
    problem = Problem(solver) if solver is not None else Problem()
    for variable, domain in variables_domains:
        problem.addVariable(variable, domain)
    problem.addConstraint(
        constraint_factory(), [variable for variable, _ in variables_domains]
    )
    return set(
        tuple(sorted(solution.items())) for solution in problem.getSolutions()
    )


def preprocess(variables_domains, constraint):
    domains = dict(
        (variable, Domain(domain)) for variable, domain in variables_domains
    )
    variables = [variable for variable, _ in variables_domains]
    constraint.preProcess(variables, domains, [], {})
    return domains


CASES = [
    # Hall set: three variables, two values. No solution exists.
    [("a", [1, 2]), ("b", [1, 2]), ("c", [1, 2])],
    # Hall set on {a, b} which only prunes c before branching.
    [("a", [1, 2]), ("b", [1, 2]), ("c", [1, 2, 3])],
    # Nothing prunable: every value belongs to some complete matching.
    [("a", [1, 2]), ("b", [1, 2])],
    [("a", [1, 2, 3]), ("b", [1, 2])],
    # Mixed domains with nested Hall structure.
    [("a", [1, 2, 3]), ("b", [1, 2, 3, 4]), ("c", [2, 3]), ("d", [1, 4])],
    [("a", [1, 2]), ("b", [2, 3]), ("c", [1, 3]), ("d", [1, 2, 3, 4])],
    # Full permutation problem.
    [("a", [1, 2, 3, 4]), ("b", [1, 2, 3, 4]),
     ("c", [1, 2, 3, 4]), ("d", [1, 2, 3, 4])],
]


def test_same_solutions_as_lightweight_constraint():
    for case in CASES:
        expected = solve_all(case, AllDifferentConstraint)
        assert solve_all(case, AllDifferentMatchingConstraint) == expected
        assert solve_all(
            case, AllDifferentMatchingConstraint, RecursiveBacktrackingSolver()
        ) == expected


def test_same_solutions_without_forwardcheck():
    solver = BacktrackingSolver(forwardcheck=False)
    for case in CASES:
        expected = solve_all(case, AllDifferentConstraint)
        assert solve_all(case, AllDifferentMatchingConstraint, solver) == expected


def test_hall_set_prunes_before_first_branch():
    case = [("a", [1, 2]), ("b", [1, 2]), ("c", [1, 2, 3])]
    domains = preprocess(case, AllDifferentMatchingConstraint())
    assert list(domains["a"]) == [1, 2]
    assert list(domains["b"]) == [1, 2]
    assert list(domains["c"]) == [3]
    # The lightweight constraint does not prune anything there.
    lightweight = preprocess(case, AllDifferentConstraint())
    assert list(lightweight["c"]) == [1, 2, 3]


def test_unsatisfiable_detected_before_first_branch():
    case = [("a", [1, 2]), ("b", [1, 2]), ("c", [1, 2])]
    domains = preprocess(case, AllDifferentMatchingConstraint())
    assert list(domains["a"]) == []
    problem = Problem()
    problem.addVariables(["a", "b", "c"], [1, 2])
    problem.addConstraint(AllDifferentMatchingConstraint())
    assert problem.getSolution() is None
    assert problem.getSolutions() == []


def test_value_not_in_current_matching_is_kept():
    # Any single matching leaves out values which belong to some other
    # complete matching; none of them may be removed.
    case = [("a", [1, 2]), ("b", [1, 2])]
    domains = preprocess(case, AllDifferentMatchingConstraint())
    assert list(domains["a"]) == [1, 2]
    assert list(domains["b"]) == [1, 2]


def test_value_reachable_from_free_value_is_kept():
    # Value 3 is free in any matching of size two, but swapping it in
    # yields other complete matchings, so nothing may be removed.
    case = [("a", [1, 2, 3]), ("b", [1, 2])]
    domains = preprocess(case, AllDifferentMatchingConstraint())
    assert list(domains["a"]) == [1, 2, 3]
    assert list(domains["b"]) == [1, 2]


def test_nested_hall_set_pruning():
    # {c, d} only share {2, 3}, so 2 and 3 must leave every other
    # domain, which in turn forces a to 1 and b to 4.
    case = [("a", [1, 2, 3]), ("b", [1, 2, 3, 4]),
            ("c", [2, 3]), ("d", [2, 3])]
    domains = preprocess(case, AllDifferentMatchingConstraint())
    assert list(domains["a"]) == [1]
    assert list(domains["b"]) == [4]
    assert list(domains["c"]) == [2, 3]
    assert list(domains["d"]) == [2, 3]


def test_search_branches_do_not_pollute_each_other():
    # Assigning "a" hides values in other domains; backtracking must
    # restore them, which the full enumeration below relies upon.
    case = [("a", [1, 2]), ("b", [1, 2, 3]), ("c", [1, 2, 3])]
    expected = solve_all(case, AllDifferentConstraint)
    assert solve_all(case, AllDifferentMatchingConstraint) == expected
    assert len(expected) == 4


def test_constraint_is_exported():
    assert "AllDifferentMatchingConstraint" in constraint.__all__
