import constraint
import itertools

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


def _vector(solution, variables):
    return tuple(solution[variable] for variable in variables)


def _image(solution, permutation, variables):
    return tuple(solution[permutation[variable]] for variable in variables)


def _full_group(variables):
    return [
        dict(zip(variables, order))
        for order in itertools.permutations(variables)
    ]


def test_lex_leader_full_group_matches_enumerated_orbits():
    # Six identical slots differing only by name: every arrangement is
    # enumerated once per permutation of the slots.
    variables = ["slot%d" % i for i in range(6)]
    domain = [0, 1]
    group = _full_group(variables)

    base = constraint.Problem()
    base.addVariables(variables, domain)
    all_solutions = base.getSolutions()
    assert len(all_solutions) == 2 ** 6

    # Enumerate every orbit of the full symmetric group and collect its
    # lexicographically smallest representative.
    expected = set()
    for solution in all_solutions:
        orbit = [_image(solution, permutation, variables) for permutation in group]
        expected.add(min(orbit))

    problem = constraint.Problem()
    problem.addVariables(variables, domain)
    problem.addConstraint(constraint.LexLeaderConstraint(group), variables)
    solutions = problem.getSolutions()

    # Compare the output representatives against the orbits, group by group.
    assert set(_vector(solution, variables) for solution in solutions) == expected
    assert len(solutions) == 7  # one sorted vector per possible count of 1s


def test_lex_leader_generators_may_keep_several_orbit_members():
    variables = ["a", "b", "c"]
    domain = [1, 2, 3]
    cycle = {"a": "b", "b": "c", "c": "a"}

    problem = constraint.Problem()
    problem.addVariables(variables, domain)
    problem.addConstraint(constraint.LexLeaderConstraint([cycle]), variables)
    solutions = set(_vector(solution, variables) for solution in problem.getSolutions())

    # Every returned solution is lexicographically smaller than or equal
    # to its image under the declared generator.
    for vector in solutions:
        solution = dict(zip(variables, vector))
        assert vector <= _image(solution, cycle, variables)

    # Generator-wise constraints do not guarantee a single representative
    # per orbit: (1, 2, 3) and (2, 3, 1) belong to the same orbit of the
    # generated cyclic group, and both are kept.
    assert (1, 2, 3) in solutions
    assert (2, 3, 1) in solutions

    # Declaring every element of the full generated group keeps exactly
    # one representative of that orbit.
    group = [
        {"a": "a", "b": "b", "c": "c"},
        {"a": "b", "b": "c", "c": "a"},
        {"a": "c", "b": "a", "c": "b"},
    ]
    problem = constraint.Problem()
    problem.addVariables(variables, domain)
    problem.addConstraint(constraint.LexLeaderConstraint(group), variables)
    solutions = set(_vector(solution, variables) for solution in problem.getSolutions())
    assert (1, 2, 3) in solutions
    assert (2, 3, 1) not in solutions
    assert (3, 1, 2) not in solutions


def test_lex_leader_explicit_value_order():
    variables = ["a", "b"]
    swap = {"a": "b", "b": "a"}
    problem = constraint.Problem()
    problem.addVariables(variables, [1, 2, 3])
    problem.addConstraint(
        constraint.LexLeaderConstraint([swap], value_order=[3, 1, 2]), variables
    )
    solutions = set(_vector(solution, variables) for solution in problem.getSolutions())
    # The explicit order ranks 3 below 1 below 2.
    assert solutions == {(3, 3), (3, 1), (3, 2), (1, 1), (1, 2), (2, 2)}


def test_lex_leader_forwardcheck_on_equal_prefix():
    variables = ["a", "b", "c", "d"]
    permutation = {"a": "b", "b": "a", "c": "d", "d": "c"}
    lex = constraint.LexLeaderConstraint([permutation])
    domains = dict((variable, constraint.Domain([1, 2, 3])) for variable in variables)
    lex.preProcess(variables, domains, [], {})

    # The prefix (a, b) is equal, so propagation continues at (c, d):
    # values of d smaller than the assigned c can never satisfy the
    # constraint and are hidden.
    assignments = {"a": 1, "b": 1, "c": 2}
    domains["d"].pushState()
    assert lex(variables, domains, assignments, forwardcheck=True)
    assert list(domains["d"]) == [2, 3]
    domains["d"].popState()
    assert sorted(domains["d"]) == [1, 2, 3]

    # An equal prefix followed by a larger value on the image side
    # satisfies the constraint regardless of the remaining positions.
    assert lex(variables, domains, {"a": 1, "b": 2, "c": 3, "d": 1})
    # An equal prefix followed by a smaller value on the image side
    # breaks it.
    assert not lex(variables, domains, {"a": 1, "b": 1, "c": 3, "d": 2})

    # Forward checking must not change the set of solutions.
    variables = ["x", "y", "z"]
    group = _full_group(variables)
    solutions = []
    for forwardcheck in (True, False):
        problem = constraint.Problem(
            constraint.BacktrackingSolver(forwardcheck=forwardcheck)
        )
        problem.addVariables(variables, [1, 2, 3])
        problem.addConstraint(constraint.LexLeaderConstraint(group), variables)
        solutions.append(
            set(_vector(solution, variables) for solution in problem.getSolutions())
        )
    assert solutions[0] == solutions[1]


def test_lex_leader_invalid_declarations_must_be_revoked():
    variables = ["a", "b"]
    swap = {"a": "b", "b": "a"}

    # Permutations which are not one-to-one are rejected right away.
    try:
        constraint.LexLeaderConstraint([{"a": "b", "b": "b"}])
    except ValueError:
        pass
    else:
        raise AssertionError("non-bijective permutation accepted")

    # Permutations which do not cover exactly the declared variables are
    # rejected when the problem is solved.
    problem = constraint.Problem()
    problem.addVariables(variables, [1, 2])
    problem.addConstraint(constraint.LexLeaderConstraint([{"a": "a"}]), variables)
    try:
        problem.getSolutions()
    except ValueError:
        pass
    else:
        raise AssertionError("incomplete permutation accepted")

    # Variables declared interchangeable must have identical domains;
    # otherwise the caller is asked to revoke the declaration instead of
    # silently losing valid answers.
    problem = constraint.Problem()
    problem.addVariable("a", [1, 2])
    problem.addVariable("b", [1, 2, 3])
    problem.addConstraint(constraint.LexLeaderConstraint([swap]), variables)
    try:
        problem.getSolutions()
    except ValueError:
        pass
    else:
        raise AssertionError("symmetry over different domains accepted")

    # Once the invalid declaration is revoked, all valid answers are
    # still there.
    problem = constraint.Problem()
    problem.addVariable("a", [1, 2])
    problem.addVariable("b", [1, 2, 3])
    assert len(problem.getSolutions()) == 6

    # Values missing from an explicit value order are rejected as well.
    problem = constraint.Problem()
    problem.addVariables(variables, [1, 2])
    problem.addConstraint(
        constraint.LexLeaderConstraint([swap], value_order=[1]), variables
    )
    try:
        problem.getSolutions()
    except ValueError:
        pass
    else:
        raise AssertionError("value missing from explicit order accepted")
