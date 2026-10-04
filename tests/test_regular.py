import itertools

import pytest

from constraint import Problem, RegularConstraint


def scheduling_automaton():
    # Shift scheduling rules over {"D"ay, "N"ight, "R"est}:
    # - three consecutive night shifts are not allowed;
    # - after a run of night shifts, a rest day is required
    #   before any day shift.
    # States are plain ints: 0 = rested/no pending night,
    # 1 = one consecutive night, 2 = two consecutive nights.
    transitions = [
        (0, "D", 0),
        (0, "R", 0),
        (0, "N", 1),
        (1, "N", 2),
        (1, "R", 0),
        (2, "R", 0),
    ]
    return transitions, [0], [0, 1, 2]


def scheduling_brute_force(days):
    def accepted(seq):
        run = 0
        for shift in seq:
            if shift == "N":
                run += 1
                if run >= 3:
                    return False
            elif shift == "D":
                if run > 0:
                    return False
            else:
                run = 0
        return True

    return set(
        seq
        for seq in itertools.product("DNR", repeat=days)
        if accepted(seq)
    )


def test_scheduling_solutions():
    days = list(range(7))  # non-string variable names
    transitions, initial, final = scheduling_automaton()
    problem = Problem()
    problem.addVariables(days, ["D", "N", "R"])
    problem.addConstraint(RegularConstraint(transitions, initial, final), days)
    solutions = problem.getSolutions()
    got = set(tuple(solution[day] for day in days) for solution in solutions)
    assert got == scheduling_brute_force(7)
    for solution in solutions:
        seq = "".join(solution[day] for day in days)
        assert "NNN" not in seq


def test_middle_domain_narrowing_prunes_and_restores():
    days = list(range(7))
    transitions, initial, final = scheduling_automaton()
    constraint = RegularConstraint(transitions, initial, final)
    problem = Problem()
    problem.addVariables(days, ["D", "N", "R"])
    problem.addConstraint(constraint, days)
    domains, constraints, vconstraints = problem._getArgs()
    assert constraints
    full = set("DNR")
    for day in days:
        assert set(domains[day]) == full

    # Enter a search branch: narrow the middle variable to {"N"}.
    for domain in domains.values():
        domain.pushState()
    domains[3].hideValue("D")
    domains[3].hideValue("R")
    assert constraint(days, domains, {}, True)

    # A remote variable is pruned accordingly: with day 3 on a night
    # shift, day 4 may not be a day shift.
    assert set(domains[3]) == {"N"}
    assert set(domains[4]) == {"N", "R"}
    for day in (0, 1, 2, 5, 6):
        assert set(domains[day]) == full

    # Retract the search branch: every domain is restored.
    for domain in domains.values():
        domain.popState()
    for day in days:
        assert set(domains[day]) == full


def test_multiple_initial_states_and_nondeterminism():
    # States are ints, not strings. State 9 is a dead initial state;
    # state 0 branches non-deterministically on "a".
    transitions = [
        (0, "a", 0),
        (0, "a", 1),
        (1, "b", 1),
        (0, "a", 0),  # duplicated transition is harmless
    ]
    initial = [0, 9]
    final = [1]
    problem = Problem()
    variables = ["x", "y", "z"]
    problem.addVariables(variables, ["a", "b"])
    problem.addConstraint(
        RegularConstraint(transitions, initial, final), variables
    )
    solutions = problem.getSolutions()
    got = set(tuple(sol[v] for v in variables) for sol in solutions)

    expected = set()
    for seq in itertools.product("ab", repeat=3):
        states = set(initial)
        for symbol in seq:
            states = set(
                target
                for source, sym, target in transitions
                if source in states and sym == symbol
            )
        if states & set(final):
            expected.add(seq)
    assert got == expected
    assert got == set(
        seq
        for seq in itertools.product("ab", repeat=3)
        if "a" not in "".join(seq).lstrip("a") and seq[0] == "a"
    )


def test_epsilon_transitions_rejected():
    with pytest.raises(ValueError):
        RegularConstraint([(0, None, 1)], [0], [1])


def test_empty_sequence():
    # Accepted exactly when an initial state is also final.
    constraint = RegularConstraint([], ["s0"], ["s0"])
    assert constraint([], {}, {})
    constraint = RegularConstraint([], ["s0"], ["s1"])
    assert not constraint([], {}, {})


def test_repeated_symbols():
    # Accept exactly the sequence ("a", "a").
    transitions = [(0, "a", 1), (1, "a", 2)]
    problem = Problem()
    problem.addVariables(["x", "y"], ["a", "b"])
    problem.addConstraint(RegularConstraint(transitions, [0], [2]), ["x", "y"])
    assert problem.getSolutions() == [{"x": "a", "y": "a"}]


def test_unreachable_final_state():
    # The only final state can never be reached: no solutions.
    transitions = [(0, "a", 0)]
    problem = Problem()
    problem.addVariables(["x", "y"], ["a", "b"])
    problem.addConstraint(RegularConstraint(transitions, [0], [1]), ["x", "y"])
    assert problem.getSolutions() == []


def test_single_variable():
    transitions, initial, final = scheduling_automaton()
    problem = Problem()
    problem.addVariable("day0", ["D", "N", "R"])
    problem.addConstraint(
        RegularConstraint(transitions, initial, final), ["day0"]
    )
    solutions = problem.getSolutions()
    assert len(solutions) == 3
