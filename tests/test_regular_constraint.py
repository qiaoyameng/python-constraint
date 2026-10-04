import pytest

from constraint import (
    BacktrackingSolver,
    Domain,
    Problem,
    RecursiveBacktrackingSolver,
    RegularConstraint,
)


def night_schedule_constraint():
    return RegularConstraint(
        transitions=[
            (0, "D", 0),
            (0, "R", 0),
            (0, "N", 1),
            (1, "R", 0),
            (1, "N", 2),
            (2, "R", 0),
        ],
        initial_states=[0],
        accepting_states=[0],
    )


def test_night_schedule_solutions():
    problem = Problem()
    problem.addVariables(range(4), ["D", "N", "R"])
    problem.addConstraint(night_schedule_constraint(), list(range(4)))

    solutions = problem.getSolutions()
    assert {0: "N", 1: "N", 2: "R", 3: "D"} in solutions
    assert {0: "N", 1: "R", 2: "N", 3: "R"} in solutions
    assert all(
        tuple(solution[i] for i in range(4)).count("N") <= 2
        for solution in solutions
    )
    assert all(
        "NNN" not in "".join(solution[i] for i in range(4))
        for solution in solutions
    )
    assert all(
        not "".join(solution[i] for i in range(4)).endswith("N")
        for solution in solutions
    )
    assert len(solutions) == 33


def test_nondeterministic_multiple_initial_states_and_non_string_names():
    state = (1, 2)
    variable = object()
    constraint = RegularConstraint(
        transitions={
            0: {1: [state, 2]},
            state: {1: 4},
            2: {1: 3},
        },
        initial_states=(0, 9),
        accepting_states=[3, 4],
    )

    other = object()
    domains = {variable: Domain([1]), other: Domain([1])}
    assignments = {variable: 1, other: 1}
    assert constraint([variable, other], domains, assignments)


def test_duplicate_symbols_are_nondeterministic_transitions():
    constraint = RegularConstraint(
        transitions=[
            (0, "a", 1),
            (0, "a", 2),
            (1, "b", 3),
            (2, "c", 3),
        ],
        initial_states=0,
        accepting_states=3,
    )

    problem = Problem()
    problem.addVariables(["x", "y"], ["a", "b", "c"])
    problem.addConstraint(constraint, ["x", "y"])

    assert {
        tuple(sorted(solution.items())) for solution in problem.getSolutions()
    } == {
        (("x", "a"), ("y", "b")),
        (("x", "a"), ("y", "c")),
    }


def test_epsilon_transitions_are_rejected():
    with pytest.raises(ValueError):
        RegularConstraint(
            transitions={(0, None): 1},
            initial_states=0,
            accepting_states=1,
        )

    with pytest.raises(ValueError):
        RegularConstraint(
            transitions=[(0, "", 1)],
            initial_states=0,
            accepting_states=1,
        )


def test_empty_sequence():
    accepted = RegularConstraint(
        transitions={},
        initial_states=[0],
        accepting_states=[0],
    )
    rejected = RegularConstraint(
        transitions={},
        initial_states=[0],
        accepting_states=[1],
    )

    accepted_problem = Problem()
    rejected_problem = Problem()
    accepted_problem.addConstraint(accepted, [])
    rejected_problem.addConstraint(rejected, [])

    assert accepted_problem.getSolution() == {}
    assert accepted_problem.getSolutions() == [{}]
    assert rejected_problem.getSolution() is None
    assert rejected_problem.getSolutions() == []


def test_unreachable_accepting_state_does_not_accept():
    problem = Problem()
    problem.addVariable("x", ["a", "b"])
    problem.addConstraint(
        RegularConstraint(
            transitions={(0, "a"): 1},
            initial_states=0,
            accepting_states=[1, 2],
        ),
        ["x"],
    )

    assert problem.getSolutions() == [{"x": "a"}]


def test_global_support_prunes_domains():
    problem = Problem()
    problem.addVariable("x", ["a", "b"])
    problem.addVariable("y", ["a", "b"])
    problem.addConstraint(
        RegularConstraint(
            transitions=[
                (0, "a", 1),
                (1, "b", 2),
            ],
            initial_states=0,
            accepting_states=2,
        ),
        ["x", "y"],
    )

    assert problem.getSolutions() == [{"x": "a", "y": "b"}]


def test_remote_domain_pruning_is_rolled_back():
    variables = ["x", "y", "z"]
    domains = {
        "x": Domain(["a", "x"]),
        "y": Domain(["b", "y"]),
        "z": Domain(["c", "z"]),
    }
    regular = RegularConstraint(
        transitions=[
            (0, "a", 1),
            (0, "x", 2),
            (1, "b", 3),
            (2, "y", 4),
            (3, "c", 5),
            (4, "z", 5),
        ],
        initial_states=0,
        accepting_states=5,
    )

    problem = Problem(BacktrackingSolver())
    problem._variables.update(domains)
    problem.addConstraint(regular, variables)
    prepared_domains, _constraints, vconstraints = problem._getArgs()
    baseline = {
        variable: list(domain)
        for variable, domain in prepared_domains.items()
    }

    prepared_domains["y"].pushState()
    prepared_domains["y"].hideValue("y")
    for variable in ("x", "z"):
        prepared_domains[variable].pushState()
    assert regular(variables, prepared_domains, {}, True)
    assert list(prepared_domains["y"]) == ["b"]
    assert list(prepared_domains["x"]) == ["a"]
    assert list(prepared_domains["z"]) == ["c"]

    for variable in ("z", "x"):
        prepared_domains[variable].popState()
    prepared_domains["y"].popState()

    for variable in variables:
        assert list(prepared_domains[variable]) == baseline[variable]
    assert vconstraints


@pytest.mark.parametrize(
    "solver",
    [BacktrackingSolver(), RecursiveBacktrackingSolver()],
)
def test_solvers_prune_and_roll_back(solver):
    problem = Problem(solver)
    problem.addVariables(range(4), ["D", "N", "R"])
    problem.addConstraint(night_schedule_constraint(), list(range(4)))

    assert len(problem.getSolutions()) == 33
