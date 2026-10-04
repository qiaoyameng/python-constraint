import pytest

import constraint
from constraint import (
    BacktrackingSolver,
    CumulativeConstraint,
    Problem,
    RecursiveBacktrackingSolver,
)

from examples.abc import abc
from examples.coins import coins

# from examples.crosswords import crosswords
from examples.einstein import einstein
from examples.queens import queens
from examples.rooks import rooks
from examples.studentdesks import studentdesks

# from examples.sudoku import sudoku
# from examples.wordmath import (seisseisdoze, sendmoremoney, twotwofour)
# from examples.xsum import xsum

import constraint.compat as compat


def test_abc():
    solutions = abc.solve()
    minvalue, minsolution = solutions
    assert minvalue == 37
    assert minsolution == {"a": 1, "c": 2, "b": 1}


def test_coins():
    solutions = coins.solve()
    assert len(solutions) == 2


def test_einstein():
    solutions = einstein.solve()
    expected_solutions = [
        {
            "nationality2": "dane",
            "nationality3": "brit",
            "nationality1": "norwegian",
            "nationality4": "german",
            "nationality5": "swede",
            "color1": "yellow",
            "color3": "red",
            "color2": "blue",
            "color5": "white",
            "color4": "green",
            "drink4": "coffee",
            "drink5": "beer",
            "drink1": "water",
            "drink2": "tea",
            "drink3": "milk",
            "smoke5": "bluemaster",
            "smoke4": "prince",
            "smoke3": "pallmall",
            "smoke2": "blends",
            "smoke1": "dunhill",
            "pet5": "dogs",
            "pet4": "fish",
            "pet1": "cats",
            "pet3": "birds",
            "pet2": "horses",
        }
    ]
    assert solutions == expected_solutions


def test_queens():
    solutions, size = queens.solve()
    assert size == 8
    for solution in solutions:
        queens.showSolution(solution, size)


def test_rooks():
    size = 8
    solutions = rooks.solve(size)
    assert len(solutions) == rooks.factorial(size)


def test_studentdesks():
    solutions = studentdesks.solve()
    expected_solutions = {
        1: "A",
        2: "E",
        3: "D",
        4: "E",
        5: "D",
        6: "A",
        7: "C",
        8: "B",
        9: "C",
        10: "B",
        11: "E",
        12: "D",
        13: "E",
        14: "D",
        15: "A",
        16: "C",
        17: "B",
        18: "C",
        19: "B",
        20: "A",
    }
    assert solutions == expected_solutions


def test_constraint_without_variables():
    problem = constraint.Problem()
    problem.addVariable("a", [1, 2, 3])
    problem.addConstraint(lambda a: a * 2 == 6)
    solutions = problem.getSolutions()
    assert solutions == [{"a": 3}]


def test_version():
    assert isinstance(constraint.__version__, compat.string_types)


def test_cumulative_negative_starts_and_half_open_interval():
    problem = Problem()
    problem.addVariables(["a", "b"], [-1, 0])
    problem.addConstraint(CumulativeConstraint(1, [1, 1], [1, 1]))

    assert problem.getSolutions() == [
        {"a": 0, "b": -1},
        {"a": -1, "b": 0},
    ]


def test_cumulative_allows_touching_intervals():
    problem = Problem()
    problem.addVariable("a", [0])
    problem.addVariable("b", [0, 1])
    problem.addConstraint(CumulativeConstraint(1, [1, 1], [1, 1]))

    assert problem.getSolution() == {"a": 0, "b": 1}


def test_cumulative_handles_peak_from_three_tasks():
    problem = Problem()
    problem.addVariables(["a", "b", "c"], [0, 1])
    problem.addConstraint(CumulativeConstraint(2, [1, 1, 1], [1, 1, 1]))

    solutions = problem.getSolutions()

    assert len(solutions) == 6
    assert {"a": 0, "b": 0, "c": 0} not in solutions
    assert {"a": 1, "b": 1, "c": 1} not in solutions


def test_cumulative_zero_duration_does_not_use_capacity():
    problem = Problem()
    problem.addVariables(["a", "b"], [0])
    problem.addConstraint(CumulativeConstraint(1, [1, 0], [1, 5]))

    assert problem.getSolution() == {"a": 0, "b": 0}


def test_cumulative_capacity_shortage_is_unsatisfiable():
    problem = Problem()
    problem.addVariables(["a", "b"], [0])
    problem.addConstraint(CumulativeConstraint(1, [1, 1], [1, 1]))

    assert problem.getSolution() is None
    assert problem.getSolutions() == []


def test_cumulative_treats_empty_pruned_domain_as_unsatisfiable():
    problem = Problem()
    problem.addVariable("a", [0])
    problem.addVariable("b", [0, 1])
    problem.addConstraint(lambda b: False, ["b"])
    problem.addConstraint(CumulativeConstraint(1, [1, 1], [1, 1]))

    assert problem.getSolution() is None
    assert problem.getSolutions() == []


def test_cumulative_prunes_impossible_start_domains():
    problem = Problem()
    problem.addVariable("a", [0])
    problem.addVariable("b", [-1, 1, 2])
    problem.addConstraint(CumulativeConstraint(1, [2, 2], [1, 1]))

    domains, _, _ = problem._getArgs()

    assert list(domains["a"]) == [0]
    assert list(domains["b"]) == [2]


def test_cumulative_can_solve_same_problem_after_backtracking():
    problem = Problem(BacktrackingSolver())
    problem.addVariables(["a", "b", "c"], [0, 1])
    problem.addConstraint(CumulativeConstraint(2, [1, 1, 1], [1, 1, 1]))

    first_solution = problem.getSolution()

    assert first_solution == problem.getSolution()


def test_cumulative_with_recursive_backtracking_solver():
    problem = Problem(RecursiveBacktrackingSolver())
    problem.addVariables(["a", "b"], [0, 1])
    problem.addConstraint(CumulativeConstraint(1, [1, 1], [1, 1]))

    assert problem.getSolution() in (
        {"a": 0, "b": 1},
        {"a": 1, "b": 0},
    )


def test_cumulative_validates_integer_non_negative_task_data():
    with pytest.raises(TypeError):
        CumulativeConstraint(1, [1.0], [1])
    with pytest.raises(ValueError):
        CumulativeConstraint(1, [-1], [1])
    with pytest.raises(TypeError):
        CumulativeConstraint(1, [1], [1.0])
    with pytest.raises(ValueError):
        CumulativeConstraint(1, [1], [-1])


def test_cumulative_validates_matching_task_data_length():
    with pytest.raises(ValueError):
        CumulativeConstraint(1, [1, 1], [1])


def test_cumulative_accepts_demands_keyword():
    problem = Problem()
    problem.addVariables(["a", "b"], [0, 1])
    problem.addConstraint(CumulativeConstraint(1, [1, 1], demands=[1, 1]))

    assert len(problem.getSolutions()) == 2


def test_cumulative_uses_unit_demands_by_default():
    problem = Problem()
    problem.addVariables(["a", "b"], [0])
    problem.addConstraint(CumulativeConstraint(2, [1, 1]))

    assert problem.getSolution() == {"a": 0, "b": 0}


def test_cumulative_rejects_demand_aliases_used_together():
    with pytest.raises(ValueError):
        CumulativeConstraint(
            1,
            [1, 1],
            demands=[1, 1],
            requirements=[1, 1],
        )
