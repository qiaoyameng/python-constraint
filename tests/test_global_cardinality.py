import itertools

import pytest

from constraint import (
    BacktrackingSolver,
    Domain,
    GlobalCardinalityConstraint,
    Problem,
    RecursiveBacktrackingSolver,
    Variable,
)


def brute_force(domains, counts, closed):
    solutions = []
    variables = sorted(domains)
    for values in itertools.product(*(domains[variable] for variable in variables)):
        tally = {}
        valid = True
        for value in values:
            if closed and value not in counts:
                valid = False
                break
            tally[value] = tally.get(value, 0) + 1
        if not valid:
            continue
        for value, (low, high) in counts.items():
            count = tally.get(value, 0)
            if count < low or (high is not None and count > high):
                valid = False
                break
        if valid:
            solutions.append(dict(zip(variables, values)))
    return solutions


def normalize(solutions):
    return sorted(sorted(solution.items()) for solution in solutions)


def check_against_brute_force(domains, counts, closed):
    expected = normalize(brute_force(domains, counts, closed))
    solvers = [
        BacktrackingSolver(),
        BacktrackingSolver(forwardcheck=False),
        RecursiveBacktrackingSolver(),
    ]
    for solver in solvers:
        problem = Problem(solver)
        for variable, domain in domains.items():
            problem.addVariable(variable, domain)
        problem.addConstraint(
            GlobalCardinalityConstraint(counts, closed=closed), list(domains)
        )
        assert normalize(problem.getSolutions()) == expected


def test_shift_schedule_closed_domain():
    # Night shift needs at least 3 people, day shift at most 2,
    # everyone is either on night, day, or off.
    domains = {
        "p1": ["night", "day"],
        "p2": ["night", "off"],
        "p3": ["day", "off"],
        "p4": ["night", "day", "off"],
        "p5": ["night"],
    }
    counts = {"night": (3, None), "day": (0, 2), "off": (0, None)}
    check_against_brute_force(domains, counts, closed=True)


def test_open_domain_allows_unlisted_values():
    # Exactly 2 people on night shift; unlisted values are unbounded.
    domains = {
        "p1": ["night", "day"],
        "p2": ["night", "off"],
        "p3": ["night", "day", "off"],
    }
    counts = {"night": (2, 2)}
    check_against_brute_force(domains, counts, closed=False)


def test_closed_domain_forbids_unlisted_values():
    domains = {"p1": ["night", "day"], "p2": ["night", "day"]}
    counts = {"night": (0, None), "day": (0, None)}
    check_against_brute_force(domains, counts, closed=True)


def test_exact_counts():
    domains = {"a": [1, 2], "b": [1, 2], "c": [1, 2]}
    counts = {1: (2, 2), 2: (1, 1)}
    check_against_brute_force(domains, counts, closed=True)


def test_shifts_competing_for_the_same_people():
    # Each shift individually has enough candidates, but both shifts
    # draw from the same two people, so they cannot be staffed together.
    domains = {"p1": ["night", "day"], "p2": ["night", "day"]}

    problem = Problem()
    problem.addVariables(["p1", "p2"], ["night", "day"])
    problem.addConstraint(
        GlobalCardinalityConstraint({"night": (2, None), "day": (1, None)}),
        ["p1", "p2"],
    )
    assert problem.getSolutions() == []

    night_only = Problem()
    night_only.addVariables(["p1", "p2"], ["night", "day"])
    night_only.addConstraint(
        GlobalCardinalityConstraint({"night": (2, None), "day": (0, None)}),
        ["p1", "p2"],
    )
    assert night_only.getSolutions() == [{"p1": "night", "p2": "night"}]

    day_only = Problem()
    day_only.addVariables(["p1", "p2"], ["night", "day"])
    day_only.addConstraint(
        GlobalCardinalityConstraint({"night": (0, None), "day": (1, None)}),
        ["p1", "p2"],
    )
    assert len(day_only.getSolutions()) == 3

    check_against_brute_force(domains, {"night": (2, None), "day": (1, None)}, True)
    check_against_brute_force(domains, {"night": (1, None), "day": (1, None)}, True)


def test_invalid_bounds():
    with pytest.raises(ValueError):
        GlobalCardinalityConstraint({"night": (3, 2)})
    with pytest.raises(ValueError):
        GlobalCardinalityConstraint({"night": (-1, 2)})
    with pytest.raises(ValueError):
        GlobalCardinalityConstraint({"night": (1.5, 2)})
    with pytest.raises(ValueError):
        GlobalCardinalityConstraint({"night": 3})
    with pytest.raises(ValueError):
        GlobalCardinalityConstraint([("night", (1, 2))])


def test_duplicated_variables():
    problem = Problem()
    problem.addVariable("a", [1, 2])
    problem.addConstraint(GlobalCardinalityConstraint({1: (1, 1)}), ["a", "a"])
    with pytest.raises(ValueError):
        problem.getSolution()


def test_assigned_count_over_max():
    constraint = GlobalCardinalityConstraint({"night": (0, 1), "day": (0, 1)})
    variables = ["a", "b"]
    domains = {"a": Domain(["night"]), "b": Domain(["night", "day"])}
    assert constraint(variables, domains, {"a": "night"})
    assert not constraint(variables, domains, {"a": "night", "b": "night"})


def test_closed_rejects_unlisted_assignment():
    variables = ["a"]
    domains = {"a": Domain(["night", "day"])}
    closed = GlobalCardinalityConstraint({"night": (0, 5)}, closed=True)
    assert not closed(variables, domains, {"a": "day"})
    opened = GlobalCardinalityConstraint({"night": (0, 5)}, closed=False)
    assert opened(variables, domains, {"a": "day"})


def test_forwardcheck_accounts_for_shared_variables():
    # x4 can only take "b", exhausting b's capacity, so "b" must be
    # hidden from x1..x3. Reasoning about each value independently
    # would not prune anything here.
    constraint = GlobalCardinalityConstraint({"a": (2, 3), "b": (1, 1)})
    x1, x2, x3, x4 = variables = [Variable("x%d" % i) for i in range(1, 5)]
    domains = {
        x1: Domain(["a", "b"]),
        x2: Domain(["a", "b"]),
        x3: Domain(["a", "b"]),
        x4: Domain(["b"]),
    }
    assert constraint(variables, domains, {})
    assert constraint(variables, domains, {}, True)
    assert list(domains[x1]) == ["a"]
    assert list(domains[x2]) == ["a"]
    assert list(domains[x3]) == ["a"]
    assert list(domains[x4]) == ["b"]


def test_forwardcheck_empty_domain():
    constraint = GlobalCardinalityConstraint({"a": (2, 2)})
    x1, x2 = variables = [Variable("x1"), Variable("x2")]
    domains = {x1: Domain(["a"]), x2: Domain(["b"])}
    assert not constraint(variables, domains, {}, True)


def test_hidden_values_restored_on_pop():
    constraint = GlobalCardinalityConstraint({"a": (2, 3), "b": (1, 1)})
    x1, x2, x3, x4 = variables = [Variable("x%d" % i) for i in range(1, 5)]
    domains = {
        x1: Domain(["a", "b"]),
        x2: Domain(["a", "b"]),
        x3: Domain(["a", "b"]),
        x4: Domain(["b"]),
    }
    for domain in domains.values():
        domain.pushState()
    assert constraint(variables, domains, {}, True)
    assert list(domains[x1]) == ["a"]
    for domain in domains.values():
        domain.popState()
    assert list(domains[x1]) == ["a", "b"]
    assert list(domains[x2]) == ["a", "b"]
    assert list(domains[x3]) == ["a", "b"]
    assert list(domains[x4]) == ["b"]
