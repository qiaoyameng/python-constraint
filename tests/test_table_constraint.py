import pytest

from constraint import BacktrackingSolver, Problem, TableConstraint


def test_empty_table_removes_all_solutions():
    problem = Problem()
    problem.addVariables(["a", "b"], [0, 1])
    problem.addConstraint(TableConstraint([]), ["a", "b"])

    assert problem.getSolutions() == []


def test_single_column_and_duplicate_rows():
    problem = Problem()
    problem.addVariable("a", [0, 1, 2, 3])
    problem.addConstraint(TableConstraint([(1,), [1], (2,), (2,)]), ["a"])

    assert problem.getSolutions() == [{"a": 2}, {"a": 1}]


def test_three_column_crossing_support():
    rows = [(0, 0, 0), (0, 0, 1), (0, 1, 0), (1, 0, 0)]
    problem = Problem(BacktrackingSolver(False))
    problem.addVariables(["a", "b", "c"], [0, 1, 2])
    problem.addConstraint(TableConstraint(rows), ["a", "b", "c"])

    solutions = problem.getSolutions()

    assert solutions == [
        {"a": 1, "b": 0, "c": 0},
        {"a": 0, "b": 1, "c": 0},
        {"a": 0, "b": 0, "c": 1},
        {"a": 0, "b": 0, "c": 0},
    ]


def test_invalid_row_lengths_are_rejected():
    with pytest.raises(ValueError):
        TableConstraint([(0, 0), (1,)])

    problem = Problem()
    problem.addVariables(["a", "b"], [0, 1])

    with pytest.raises(ValueError):
        problem.addConstraint(TableConstraint([(0,), (1,)]), ["a", "b"])


def test_active_support_state_is_restored_on_backtracking():
    rows = [(0, 0, 0), (0, 0, 1), (0, 1, 0), (1, 0, 0)]
    problem = Problem(BacktrackingSolver())
    problem.addVariables(["a", "b", "c"], [0, 1, 2])
    problem.addConstraint(TableConstraint(rows), ["a", "b", "c"])
    problem.addConstraint(lambda a: a == 1, ["a"])

    assert problem.getSolutions() == [{"a": 1, "b": 0, "c": 0}]


def test_shared_definition_keeps_search_state_separate():
    table = TableConstraint([(0, 0), (1, 1)])
    problem1 = Problem()
    problem2 = Problem()
    problem1.addVariables(["a", "b"], [0, 1])
    problem2.addVariables(["a", "b"], [0, 1])
    problem1.addConstraint(table, ["a", "b"])
    problem2.addConstraint(table, ["a", "b"])

    domains1, constraints1, _ = problem1._getArgs()
    domains2, constraints2, _ = problem2._getArgs()
    compiled1 = constraints1[0][0]
    compiled2 = constraints2[0][0]

    assert compiled1 is not compiled2

    domains1["a"].pushState()
    domains1["a"].hideValue(0)

    assert compiled1._active_counts[0] == 1
    assert compiled2._active_counts[0] == 2


def test_repeated_constraint_bindings_are_compiled_independently():
    table = TableConstraint([(0, 0), (1, 1)])
    problem = Problem()
    problem.addVariables(["a", "b"], [0, 1])
    problem.addConstraint(table, ["a", "b"])
    problem.addConstraint(table, ["a", "b"])

    _, constraints, _ = problem._getArgs()

    assert len(constraints) == 2
    assert constraints[0][0] is not constraints[1][0]
    assert problem.getSolutions() == [{"a": 1, "b": 1}, {"a": 0, "b": 0}]


def test_propagation_visits_only_table_candidates():
    rows = [(value, value, value) for value in range(40)]
    rows.append((0, 1, 39))
    table = TableConstraint(rows)
    problem = Problem(BacktrackingSolver())
    problem.addVariables(["a", "b", "c"], range(100))
    problem.addConstraint(table, ["a", "b", "c"])

    domains, constraints, _ = problem._getArgs()
    compiled = constraints[0][0]
    variables = ["a", "b", "c"]

    for variable in ("b", "c"):
        domains[variable].pushState()

    assert compiled(variables, domains, {"a": 0}, True)
    assert compiled._candidate_accesses == 2
    assert list(domains["b"]) == [0, 1]
    assert list(domains["c"]) == [0, 39]
    assert compiled._candidate_accesses < 100 ** 3
