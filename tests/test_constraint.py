import constraint

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


def test_cumulative_constraint_with_negative_start_times():
    problem = constraint.Problem()
    problem.addVariables(["a", "b", "c"], [-1, 0, 1])
    problem.addConstraint(
        constraint.CumulativeConstraint(
            4, [2, 2, 2], [2, 2, 2]
        ),
        ["a", "b", "c"],
    )

    solutions = problem.getSolutions()

    assert {"a": -1, "b": 1, "c": 1} in solutions
    assert {"a": -1, "b": -1, "c": 1} in solutions
    assert {"a": -1, "b": -1, "c": -1} not in solutions


def test_cumulative_constraint_allows_adjacent_half_open_intervals():
    problem = constraint.Problem()
    problem.addVariables(["a", "b"], [0, 1, 2])
    problem.addConstraint(
        constraint.CumulativeConstraint(1, [1, 1], [1, 1]),
        ["a", "b"],
    )

    solutions = problem.getSolutions()

    assert {"a": 0, "b": 1} in solutions
    assert {"a": 1, "b": 0} in solutions
    assert {"a": 0, "b": 0} not in solutions


def test_cumulative_constraint_detects_three_task_peak():
    problem = constraint.Problem()
    problem.addVariables(["a", "b", "c"], [0, 1, 2])
    problem.addConstraint(
        constraint.CumulativeConstraint(
            4, [2, 2, 2], [2, 2, 2]
        ),
        ["a", "b", "c"],
    )

    solutions = problem.getSolutions()

    assert len(solutions) == 12
    assert {"a": 0, "b": 0, "c": 0} not in solutions
    assert {"a": 0, "b": 2, "c": 2} in solutions


def test_cumulative_constraint_with_zero_duration_and_capacity_exceeded():
    problem = constraint.Problem()
    problem.addVariables(["a", "b", "c"], [0])
    problem.addConstraint(
        constraint.CumulativeConstraint(
            1, [1, 1, 0], [1, 1, 2]
        ),
        ["a", "b", "c"],
    )

    assert problem.getSolution() is None
    assert problem.getSolutions() == []


def test_cumulative_constraint_returns_no_solution_for_empty_domain():
    problem = constraint.Problem()
    problem.addVariable("a", [0, 1])
    problem.addVariable("b", [0])
    problem.addConstraint(
        constraint.CumulativeConstraint(1, [1, 2], [1, 1]),
        ["a", "b"],
    )

    assert problem.getSolution() is None
    assert problem.getSolutions() == []


def test_cumulative_constraint_can_be_solved_repeatedly():
    problem = constraint.Problem()
    problem.addVariables(["a", "b", "c"], [-1, 0, 1])
    problem.addConstraint(
        constraint.CumulativeConstraint(
            4, [2, 2, 2], [2, 2, 2]
        ),
        ["a", "b", "c"],
    )

    first_solutions = problem.getSolutions()
    second_solutions = problem.getSolutions()

    assert first_solutions == second_solutions
    assert problem.getSolution() == problem.getSolution()


def test_version():
    assert isinstance(constraint.__version__, compat.string_types)
