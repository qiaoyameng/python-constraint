from constraint import (
    Problem,
    BacktrackingSolver,
    AllDifferentConstraint,
    Constraint,
    InSetConstraint,
    RecursiveBacktrackingSolver,
)


HIDDEN_COUNT = 8
HIDDEN_VARIABLES = ["witness_%d" % i for i in range(HIDDEN_COUNT)]
VISIBLE_VARIABLES = ["m0", "m1"]


class BranchCounter(Constraint):
    """
    Count every value trial on a hidden variable without pruning anything.

    The number of calls measures how much of the hidden witness subtree the
    solver actually walks: a real projection search grows with the number of
    distinct visible assignments, while enumerating full solutions first
    would visit one branch per auxiliary completion.
    """

    def __init__(self, variables):
        self.variables = list(variables)
        self.calls = 0

    def __call__(self, variables, domains, assignments, forwardcheck=False):
        self.calls += 1
        return True


def deployment_problem():
    # Every feasible machine assignment admits 2 ** HIDDEN_COUNT auxiliary
    # boolean completions (the witnesses are unconstrained witnesses).
    problem = Problem(BacktrackingSolver())
    problem.addVariables(VISIBLE_VARIABLES, [0, 1])
    problem.addVariables(HIDDEN_VARIABLES, [False, True])
    problem.addConstraint(AllDifferentConstraint(), VISIBLE_VARIABLES)
    counter = BranchCounter(HIDDEN_VARIABLES)
    problem.addConstraint(counter, HIDDEN_VARIABLES)
    return problem, counter


def complete_solutions(problem):
    return [
        dict(solution)
        for solution in problem.getSolutions()
    ]


def test_projection_enumerates_distinct_visible_assignments():
    problem, _ = deployment_problem()
    projections = list(problem.getProjectionIter(VISIBLE_VARIABLES))

    assert sorted(
        (item["m0"], item["m1"]) for item in projections
    ) == [(0, 1), (1, 0)]
    # No duplicates, even though each projection has hundreds of completions.
    assert len(projections) == 2


def test_projection_result_contains_only_visible_variables():
    problem, _ = deployment_problem()
    projections = list(problem.getProjectionIter(["m0"]))
    assert sorted(projections, key=lambda item: item["m0"]) == [
        {"m0": 0},
        {"m0": 1},
    ]
    for projection in projections:
        assert set(projection) == {"m0"}


def test_hidden_branches_are_not_fully_enumerated():
    problem, counter = deployment_problem()
    full = complete_solutions(problem)
    full_calls = counter.calls

    assert len(full) == 2 * 2 ** HIDDEN_COUNT

    problem, counter = deployment_problem()
    projections = list(problem.getProjectionIter(VISIBLE_VARIABLES))
    projection_calls = counter.calls

    assert len(projections) == 2
    # The projection search blocks each visible assignment on the fly and
    # never walks the witness subtree again: it visits far fewer hidden
    # branches than full enumeration (32 vs ~1000 with 8 witnesses).
    assert projection_calls < full_calls // 10


def test_projection_with_no_feasible_witness_is_absent():
    problem = Problem(BacktrackingSolver())
    problem.addVariable("m", [0, 1, 2])
    problem.addVariable("w", [1, 2])
    # m == 0 cannot be witnessed; m == 1 is witnessed by w == 1 and
    # m == 2 by either witness value.
    problem.addConstraint(lambda m, w: m == w, ["m", "w"])

    projections = list(problem.getProjectionIter(["m"]))
    assert sorted(item["m"] for item in projections) == [1, 2]


def test_empty_projection_satisfiable_yields_one_empty_result():
    problem = Problem(BacktrackingSolver())
    problem.addVariables(HIDDEN_VARIABLES, [False, True])
    assert list(problem.getProjectionIter([])) == [{}]


def test_empty_projection_unsatisfiable_yields_nothing():
    problem = Problem(BacktrackingSolver())
    problem.addVariables(HIDDEN_VARIABLES, [False, True])
    problem.addConstraint(lambda w: False, ["witness_0"])
    assert list(problem.getProjectionIter([])) == []


def test_all_visible_variables_reproduces_every_solution_once():
    problem = Problem(BacktrackingSolver())
    problem.addVariables(["a", "b"], [1, 2, 3])
    problem.addConstraint(lambda a, b: b > a, ["a", "b"])

    projections = list(problem.getProjectionIter(["a", "b"]))
    assert sorted(sorted(item.items()) for item in projections) == [
        [("a", 1), ("b", 2)],
        [("a", 1), ("b", 3)],
        [("a", 2), ("b", 3)],
    ]


def test_blocking_information_does_not_modify_problem():
    problem, _ = deployment_problem()
    original = complete_solutions(problem)

    list(problem.getProjectionIter(VISIBLE_VARIABLES))

    # Same Problem, same answers, after a projection session is closed.
    assert complete_solutions(problem) == original
    assert len(problem._constraints) == 2


def test_early_close_keeps_the_problem_and_future_solves_intact():
    problem, _ = deployment_problem()
    iterator = problem.getProjectionIter(VISIBLE_VARIABLES)
    first = next(iterator)
    iterator.close()

    assert first in ({"m0": 0, "m1": 1}, {"m0": 1, "m1": 0})
    assert len(complete_solutions(problem)) == 2 * 2 ** HIDDEN_COUNT
    future = list(problem.getProjectionIter(VISIBLE_VARIABLES))
    assert len(future) == 2


def test_two_interleaved_iterators_are_independent():
    problem_a, _ = deployment_problem()
    problem_b, _ = deployment_problem()

    iterator_a = problem_a.getProjectionIter(VISIBLE_VARIABLES)
    iterator_b = problem_b.getProjectionIter(["m0"])

    first_a = next(iterator_a)
    first_b = next(iterator_b)

    second_a = next(iterator_a)
    second_b = next(iterator_b)

    assert first_a != second_a
    assert sorted(
        (item["m0"], item["m1"]) for item in (first_a, second_a)
    ) == [(0, 1), (1, 0)]
    assert first_b != second_b
    assert sorted(item["m0"] for item in (first_b, second_b)) == [0, 1]

    for iterator in (iterator_a, iterator_b):
        try:
            next(iterator)
        except StopIteration:
            pass

    assert len(complete_solutions(problem_a)) == 2 * 2 ** HIDDEN_COUNT
    assert len(complete_solutions(problem_b)) == 2 * 2 ** HIDDEN_COUNT


def test_two_interleaved_iterators_on_same_problem_are_independent():
    problem, _ = deployment_problem()

    iterator_a = problem.getProjectionIter(["m0"])
    iterator_b = problem.getProjectionIter(["m1"])

    sequence = [next(iterator_a), next(iterator_b),
                next(iterator_a), next(iterator_b)]

    assert [item["m0"] for item in sequence if "m0" in item] == [1, 0]
    assert [item["m1"] for item in sequence if "m1" in item] == [0, 1]

    for iterator in (iterator_a, iterator_b):
        try:
            next(iterator)
        except StopIteration:
            pass

    solutions = complete_solutions(problem)
    assert len(solutions) == 2 * 2 ** HIDDEN_COUNT
    assert len(set(tuple(sorted(item.items())) for item in solutions)) == len(
        solutions
    )


def test_iteration_interleaved_with_ordinary_solve():
    problem, _ = deployment_problem()
    iterator = problem.getProjectionIter(VISIBLE_VARIABLES)

    next(iterator)
    assert len(complete_solutions(problem)) == 2 * 2 ** HIDDEN_COUNT
    next(iterator)

    assert len(complete_solutions(problem)) == 2 * 2 ** HIDDEN_COUNT


def test_projection_respects_pretreatment_pruning():
    problem = Problem(BacktrackingSolver())
    problem.addVariables(VISIBLE_VARIABLES, [0, 1])
    problem.addVariables(HIDDEN_VARIABLES, [False, True])
    problem.addConstraint(AllDifferentConstraint(), VISIBLE_VARIABLES)
    problem.addConstraint(InSetConstraint([0]), ["m0"])

    projections = list(problem.getProjectionIter(VISIBLE_VARIABLES))
    assert projections == [{"m0": 0, "m1": 1}]


def test_unknown_variable_is_rejected():
    problem = Problem(BacktrackingSolver())
    problem.addVariable("m", [0, 1])
    try:
        list(problem.getProjectionIter(["m", "ghost"]))
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError for unknown variable")


def test_duplicate_visible_variable_is_rejected():
    problem = Problem(BacktrackingSolver())
    problem.addVariable("m", [0, 1])
    try:
        list(problem.getProjectionIter(["m", "m"]))
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError for duplicated variable")


def test_solver_without_iteration_cannot_project():
    problem = Problem(RecursiveBacktrackingSolver())
    problem.addVariables(["m", "w"], [0, 1])
    try:
        next(problem.getProjectionIter(["m"]))
    except NotImplementedError:
        pass
    else:
        raise AssertionError("Expected NotImplementedError")
