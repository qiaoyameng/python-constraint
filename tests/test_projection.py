from constraint import BacktrackingSolver
from constraint import Constraint
from constraint import Problem


class CompleteAssignmentCounter(Constraint):
    def __init__(self, variables):
        self.variables = variables
        self.complete_checks = 0

    def __call__(self, variables, domains, assignments, forwardcheck=False):
        if all(variable in assignments for variable in self.variables):
            self.complete_checks += 1
        return True


class HiddenBranchCounter(Constraint):
    def __init__(self, variable):
        self.variable = variable
        self.branch_checks = 0

    def preProcess(self, variables, domains, constraints, vconstraints):
        pass

    def __call__(self, variables, domains, assignments, forwardcheck=False):
        if self.variable in assignments:
            self.branch_checks += 1
        return True


def make_deployment_problem(hidden_count=10):
    visible_variables = ["machine_1", "machine_2"]
    hidden_variables = ["proof_%d" % index for index in range(hidden_count)]
    all_variables = visible_variables + hidden_variables

    problem = Problem(BacktrackingSolver(forwardcheck=False))
    problem.addVariables(visible_variables, ["A", "B"])
    problem.addVariables(hidden_variables, [False, True])
    counter = CompleteAssignmentCounter(all_variables)
    problem.addConstraint(counter, all_variables)
    hidden_branch_counters = []
    for variable in hidden_variables:
        branch_counter = HiddenBranchCounter(variable)
        hidden_branch_counters.append(branch_counter)
        problem.addConstraint(branch_counter, [variable])
    return (
        problem,
        counter,
        hidden_branch_counters,
        visible_variables,
        hidden_variables,
    )


def test_projection_enumerates_each_satisfiable_visible_assignment_once():
    (
        problem,
        counter,
        hidden_branch_counters,
        visible_variables,
        hidden_variables,
    ) = make_deployment_problem()

    projections = list(problem.getProjectedSolutionIter(visible_variables))
    projected_complete_checks = counter.complete_checks
    projected_hidden_branches = sum(
        branch_counter.branch_checks
        for branch_counter in hidden_branch_counters
    )

    expected = [
        {"machine_1": "A", "machine_2": "A"},
        {"machine_1": "A", "machine_2": "B"},
        {"machine_1": "B", "machine_2": "A"},
        {"machine_1": "B", "machine_2": "B"},
    ]
    assert sorted(
        (item["machine_1"], item["machine_2"]) for item in projections
    ) == sorted(
        (item["machine_1"], item["machine_2"]) for item in expected
    )
    assert all(set(item) == set(visible_variables) for item in projections)
    assert len(projections) == 4
    assert len(problem.getSolutions()) == 4 * 2 ** len(hidden_variables)
    assert projected_complete_checks == len(projections)
    assert projected_complete_checks < 4 * 2 ** len(hidden_variables)
    assert (
        projected_hidden_branches
        == len(projections) * len(hidden_variables)
    )
    assert projected_hidden_branches < 4 * 2 ** len(hidden_variables)


def test_get_solution_iter_accepts_projection_variables():
    problem, _, _, visible_variables, _ = make_deployment_problem()

    projections = list(problem.getSolutionIter(visible_variables))

    assert len(projections) == 4
    assert all(set(item) == set(visible_variables) for item in projections)


def test_empty_projection_has_one_result_when_satisfiable():
    problem, _, _, _, hidden_variables = make_deployment_problem()

    assert list(problem.getProjectedSolutionIter([])) == [{}]
    assert len(problem.getSolutions()) == 4 * 2 ** len(hidden_variables)


def test_empty_projection_has_no_result_when_unsatisfiable():
    problem = Problem()
    problem.addVariable("proof", [False, True])
    problem.addConstraint(lambda proof: False, ["proof"])

    assert list(problem.getProjectedSolutionIter([])) == []


def test_projection_does_not_block_later_ordinary_solving():
    problem = Problem()
    problem.addVariable("visible", [1, 2, 3])
    problem.addVariable("proof", [False, True])
    problem.addConstraint(lambda visible: visible == 2, ["visible"])

    assert list(problem.getProjectedSolutionIter(["visible"])) == [
        {"visible": 2}
    ]
    assert list(problem._variables["visible"]) == [1, 2, 3]
    assert len(problem._constraints) == 1

    assert problem.getSolutions() == [
        {"proof": True, "visible": 2},
        {"proof": False, "visible": 2},
    ]
    assert len(problem._constraints) == 1


def test_closed_projection_iterator_does_not_affect_problem():
    problem, _, _, visible_variables, hidden_variables = (
        make_deployment_problem()
    )
    iterator = problem.getProjectedSolutionIter(visible_variables)

    first = next(iterator)
    iterator.close()

    assert set(first) == set(visible_variables)
    assert len(problem.getSolutions()) == 4 * 2 ** len(hidden_variables)

    restarted = problem.getProjectedSolutionIter(visible_variables)
    assert len(list(restarted)) == 4


def test_interleaved_projection_iterators_are_independent():
    problem, _, _, visible_variables, _ = make_deployment_problem()
    first = problem.getProjectedSolutionIter(visible_variables)
    second = problem.getProjectedSolutionIter(visible_variables)

    assert next(first) == next(second)
    assert next(first) == next(second)

    remaining_first = list(first)
    remaining_second = list(second)

    assert len(remaining_first) == 2
    assert remaining_first == remaining_second
