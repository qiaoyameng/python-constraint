from constraint import BacktrackingSolver
from constraint import Problem
from constraint import TableConstraint

import pytest


def get_table_state(problem, table, variables):
    domains, _constraints, _vconstraints = problem._getArgs()
    return table._getState(tuple(variables), domains), domains


def test_empty_table_has_no_solution():
    problem = Problem()
    problem.addVariables(["a", "b"], [1, 2])
    problem.addConstraint(TableConstraint([]), ["a", "b"])

    assert problem.getSolution() is None
    assert problem.getSolutions() == []


def test_single_column_constraint():
    table = TableConstraint([(1,), (1,), (3,)])
    problem = Problem()
    problem.addVariable("a", [1, 2, 3])
    problem.addConstraint(table, ["a"])

    assert problem.getSolutions() == [{"a": 3}, {"a": 1}]
    assert table._rows == [(1,), (3,)]


def test_tuple_order_matches_variable_order():
    table = TableConstraint([(1, 2)])

    problem = Problem()
    problem.addVariables(["a", "b"], [1, 2])
    problem.addConstraint(table, ["a", "b"])
    assert problem.getSolution() == {"a": 1, "b": 2}

    problem = Problem()
    problem.addVariables(["a", "b"], [1, 2])
    problem.addConstraint(table, ["b", "a"])
    assert problem.getSolution() == {"a": 2, "b": 1}


def test_rows_with_different_lengths_are_rejected_immediately():
    with pytest.raises(ValueError):
        TableConstraint([(1, 2), (3,)])


def test_table_arity_must_match_declared_variables():
    problem = Problem()
    problem.addVariables(["a", "b", "c"], [1, 2])
    problem.addConstraint(TableConstraint([(1, 2), (2, 1)]), ["a", "b", "c"])

    with pytest.raises(ValueError):
        problem.getSolution()


def test_three_columns_with_crossing_supports():
    rows = [(1, 2, 3), (2, 3, 1), (3, 1, 2)]
    table = TableConstraint(rows)
    problem = Problem(BacktrackingSolver())
    variables = ("a", "b", "c")
    problem.addVariables(variables, range(50))
    problem.addConstraint(table, variables)

    state, domains = get_table_state(problem, table, variables)
    for domain in domains.values():
        domain.pushState()

    assert table(variables, domains, {"a": 1}, True)
    assert list(domains["b"]) == [2]
    assert list(domains["c"]) == [3]
    assert state.candidate_accesses == 1
    assert state.candidate_accesses < 50 ** 3

    for domain in domains.values():
        domain.popState()
    assert state.active == {0, 1, 2}
    assert sorted(problem.getSolutions(), key=lambda solution: solution["a"]) == [
        {"a": 1, "b": 2, "c": 3},
        {"a": 2, "b": 3, "c": 1},
        {"a": 3, "b": 1, "c": 2},
    ]


def test_shared_constraint_definition_keeps_separate_search_state():
    rows = [(1, 2, 3), (2, 3, 1), (3, 1, 2)]
    table = TableConstraint(rows)
    variables = ("a", "b", "c")

    first = Problem(BacktrackingSolver())
    first.addVariables(variables, range(50))
    first.addConstraint(table, variables)
    first_state, first_domains = get_table_state(first, table, variables)

    second = Problem(BacktrackingSolver())
    second.addVariables(variables, range(50))
    second.addConstraint(table, variables)
    second_state, _second_domains = get_table_state(second, table, variables)

    assert first_state is not second_state

    for domain in first_domains.values():
        domain.pushState()
    assert table(variables, first_domains, {"a": 1}, True)
    assert first_state.active == {0}
    assert second_state.active == {0, 1, 2}


def test_repeated_solves_rebuild_active_tuple_state():
    problem = Problem(BacktrackingSolver())
    problem.addVariables(["a", "b"], [1, 2, 3])
    table = TableConstraint([(1, 2), (2, 3)])
    problem.addConstraint(table, ["a", "b"])

    first_solutions = problem.getSolutions()
    second_solutions = problem.getSolutions()

    assert first_solutions == second_solutions
    assert second_solutions == [{"a": 2, "b": 3}, {"a": 1, "b": 2}]
