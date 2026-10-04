#!/usr/bin/python
#
# Copyright (c) 2005-2014 - Gustavo Niemeyer <gustavo@niemeyer.net>
#
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""
@var Unassigned: Helper object instance representing unassigned values

@sort: Problem, Variable, Domain
@group Solvers: Solver,
                BacktrackingSolver,
                RecursiveBacktrackingSolver,
                MinConflictsSolver,
                LexicographicBacktrackingSolver
@group Optimization: LinearExpr,
                     OptimizationResult
@group Constraints: Constraint,
                    FunctionConstraint,
                    AllDifferentConstraint,
                    AllEqualConstraint,
                    MaxSumConstraint,
                    ExactSumConstraint,
                    MinSumConstraint,
                    InSetConstraint,
                    NotInSetConstraint,
                    SomeInSetConstraint,
                    SomeNotInSetConstraint
"""

from __future__ import absolute_import, division, print_function


from .version import __author__  # noqa
from .version import __copyright__  # noqa
from .version import __credits__  # noqa
from .version import __license__  # noqa
from .version import __version__  # noqa
from .version import __email__  # noqa
from .version import __status__  # noqa
from .version import __url__  # noqa

import random
import copy
from .compat import xrange, string_types

__all__ = [
    "Problem",
    "Variable",
    "Domain",
    "Unassigned",
    "Solver",
    "BacktrackingSolver",
    "RecursiveBacktrackingSolver",
    "MinConflictsSolver",
    "LexicographicBacktrackingSolver",
    "Constraint",
    "FunctionConstraint",
    "AllDifferentConstraint",
    "AllEqualConstraint",
    "MaxSumConstraint",
    "ExactSumConstraint",
    "MinSumConstraint",
    "InSetConstraint",
    "NotInSetConstraint",
    "SomeInSetConstraint",
    "SomeNotInSetConstraint",
    "LinearExpr",
    "OptimizationResult",
]


class Problem(object):
    """
    Class used to define a problem and retrieve solutions
    """

    def __init__(self, solver=None):
        """
        @param solver: Problem solver used to find solutions
                       (default is L{BacktrackingSolver})
        @type solver:  instance of a L{Solver} subclass
        """
        self._solver = solver or BacktrackingSolver()
        self._constraints = []
        self._variables = {}

    def reset(self):
        """
        Reset the current problem definition

        Example:

        >>> problem = Problem()
        >>> problem.addVariable("a", [1, 2])
        >>> problem.reset()
        >>> problem.getSolution()
        >>>
        """
        del self._constraints[:]
        self._variables.clear()

    def setSolver(self, solver):
        """
        Change the problem solver currently in use

        Example:

        >>> solver = BacktrackingSolver()
        >>> problem = Problem(solver)
        >>> problem.getSolver() is solver
        True

        @param solver: New problem solver
        @type  solver: instance of a C{Solver} subclass
        """
        self._solver = solver

    def getSolver(self):
        """
        Obtain the problem solver currently in use

        Example:

        >>> solver = BacktrackingSolver()
        >>> problem = Problem(solver)
        >>> problem.getSolver() is solver
        True

        @return: Solver currently in use
        @rtype: instance of a L{Solver} subclass
        """
        return self._solver

    def addVariable(self, variable, domain):
        """
        Add a variable to the problem

        Example:

        >>> problem = Problem()
        >>> problem.addVariable("a", [1, 2])
        >>> problem.getSolution() in ({'a': 1}, {'a': 2})
        True

        @param variable: Object representing a problem variable
        @type  variable: hashable object
        @param domain: Set of items defining the possible values that
                       the given variable may assume
        @type  domain: list, tuple, or instance of C{Domain}
        """
        if variable in self._variables:
            msg = "Tried to insert duplicated variable %s" % repr(variable)
            raise ValueError(msg)
        if hasattr(domain, "__getitem__"):
            domain = Domain(domain)
        elif isinstance(domain, Domain):
            domain = copy.copy(domain)
        else:
            msg = "Domains must be instances of subclasses of the Domain class"
            raise TypeError(msg)
        if not domain:
            raise ValueError("Domain is empty")
        self._variables[variable] = domain

    def addVariables(self, variables, domain):
        """
        Add one or more variables to the problem

        Example:

        >>> problem = Problem()
        >>> problem.addVariables(["a", "b"], [1, 2, 3])
        >>> solutions = problem.getSolutions()
        >>> len(solutions)
        9
        >>> {'a': 3, 'b': 1} in solutions
        True

        @param variables: Any object containing a sequence of objects
                          represeting problem variables
        @type  variables: sequence of hashable objects
        @param domain: Set of items defining the possible values that
                       the given variables may assume
        @type  domain: list, tuple, or instance of C{Domain}
        """
        for variable in variables:
            self.addVariable(variable, domain)

    def addConstraint(self, constraint, variables=None):
        """
        Add a constraint to the problem

        Example:

        >>> problem = Problem()
        >>> problem.addVariables(["a", "b"], [1, 2, 3])
        >>> problem.addConstraint(lambda a, b: b == a+1, ["a", "b"])
        >>> solutions = problem.getSolutions()
        >>>

        @param constraint: Constraint to be included in the problem
        @type  constraint: instance a L{Constraint} subclass or a
                           function to be wrapped by L{FunctionConstraint}
        @param variables: Variables affected by the constraint (default to
                          all variables). Depending on the constraint type
                          the order may be important.
        @type  variables: set or sequence of variables
        """
        if not isinstance(constraint, Constraint):
            if callable(constraint):
                constraint = FunctionConstraint(constraint)
            else:
                msg = "Constraints must be instances of subclasses " "of the Constraint class"
                raise ValueError(msg)
        self._constraints.append((constraint, variables))

    def getSolution(self):
        """
        Find and return a solution to the problem

        Example:

        >>> problem = Problem()
        >>> problem.getSolution() is None
        True
        >>> problem.addVariables(["a"], [42])
        >>> problem.getSolution()
        {'a': 42}

        @return: Solution for the problem
        @rtype: dictionary mapping variables to values
        """
        domains, constraints, vconstraints = self._getArgs()
        if not domains:
            return None
        return self._solver.getSolution(domains, constraints, vconstraints)

    def getSolutions(self):
        """
        Find and return all solutions to the problem

        Example:

        >>> problem = Problem()
        >>> problem.getSolutions() == []
        True
        >>> problem.addVariables(["a"], [42])
        >>> problem.getSolutions()
        [{'a': 42}]

        @return: All solutions for the problem
        @rtype: list of dictionaries mapping variables to values
        """
        domains, constraints, vconstraints = self._getArgs()
        if not domains:
            return []
        return self._solver.getSolutions(domains, constraints, vconstraints)

    def getSolutionIter(self):
        """
        Return an iterator to the solutions of the problem

        Example:

        >>> problem = Problem()
        >>> list(problem.getSolutionIter()) == []
        True
        >>> problem.addVariables(["a"], [42])
        >>> iter = problem.getSolutionIter()
        >>> next(iter)
        {'a': 42}
        >>> next(iter)
        Traceback (most recent call last):
          File "<stdin>", line 1, in ?
        StopIteration
        """
        domains, constraints, vconstraints = self._getArgs()
        if not domains:
            return iter(())
        return self._solver.getSolutionIter(domains, constraints, vconstraints)

    def minimizeLexicographic(
        self,
        objectives,
        all_solutions=False,
        node_budget=None,
        prune=True,
        forwardcheck=True,
    ):
        """
        Find solutions minimizing a sequence of objectives lexicographically

        The first objective is the most important: among all solutions
        minimizing it, the second objective is minimized, and so on.
        This models, for instance, a scheduling rule that first minimizes
        overtime and only then balances cost across equally good schedules.

        Optimization is performed by a branch-and-bound search: at every
        node the current (possibly forward-checked) domains are used to
        compute a lower bound of each objective, and branches that cannot
        improve on the best solution found so far are pruned. Solutions
        are never collected before being compared.

        Example:

        >>> problem = Problem()
        >>> problem.addVariables(["a", "b"], [1, 2, 3])
        >>> problem.addConstraint(lambda a, b: a != b)
        >>> overtime = LinearExpr({"a": 1, "b": -1})
        >>> cost = LinearExpr({"a": 1, "b": 1}, constant=10)
        >>> result = problem.minimizeLexicographic([overtime, cost])
        >>> result.status == OptimizationResult.OPTIMAL
        True
        >>> result.objective_values
        [-2, 14]
        >>> result.solution == {"a": 1, "b": 3}
        True

        @param objectives: Sequence of integer linear expressions defining
                           the lexicographic objective. Each item is either
                           a L{LinearExpr} instance or a mapping of variables
                           to integer coefficients. The order matters.
        @type  objectives: sequence of L{LinearExpr} or dicts
        @param all_solutions: Whether to return every optimal solution
                              (default false, return a single solution)
        @type  all_solutions: bool
        @param node_budget: Maximum number of search nodes to expand.
                            When exhausted, the search stops and the result
                            status reports that the incumbent was not
                            proven optimal. None means no limit.
        @type  node_budget: int or None
        @param prune: Whether lower-bound based pruning is enabled
                      (default true)
        @type  prune: bool
        @param forwardcheck: Whether forward checking is performed while
                             assigning variables (default true)
        @type  forwardcheck: bool
        @return: An L{OptimizationResult} describing the outcome. Its
                 status distinguishes a proved optimum, an infeasible
                 problem, and an exhausted node budget.
        @rtype: L{OptimizationResult}
        """
        if not hasattr(objectives, "__getitem__") or isinstance(
            objectives, string_types
        ):
            raise TypeError("objectives must be a sequence of expressions")
        expressions = []
        for objective in objectives:
            if isinstance(objective, LinearExpr):
                expressions.append(objective)
            elif isinstance(objective, dict):
                expressions.append(LinearExpr(objective))
            else:
                raise TypeError(
                    "each objective must be a LinearExpr or a dict "
                    "of coefficients"
                )
        if not expressions:
            raise ValueError("at least one objective is required")
        if node_budget is not None and (
            isinstance(node_budget, bool)
            or not isinstance(node_budget, int)
            or node_budget <= 0
        ):
            raise ValueError("node_budget must be a positive integer or None")

        domains, constraints, vconstraints = self._getArgs()
        if not domains:
            return OptimizationResult.infeasible()

        solver = LexicographicBacktrackingSolver(
            expressions,
            prune=prune,
            forwardcheck=forwardcheck,
        )
        return solver.solve(
            domains,
            constraints,
            vconstraints,
            all_solutions=all_solutions,
            node_budget=node_budget,
        )

    def _getArgs(self):
        domains = self._variables.copy()
        allvariables = domains.keys()
        constraints = []
        for constraint, variables in self._constraints:
            if not variables:
                variables = list(allvariables)
            constraints.append((constraint, variables))
        vconstraints = {}
        for variable in domains:
            vconstraints[variable] = []
        for constraint, variables in constraints:
            for variable in variables:
                vconstraints[variable].append((constraint, variables))
        for constraint, variables in constraints[:]:
            constraint.preProcess(variables, domains, constraints, vconstraints)
        for domain in domains.values():
            domain.resetState()
            if not domain:
                return None, None, None
        # doArc8(getArcs(domains, constraints), domains, {})
        return domains, constraints, vconstraints


# ----------------------------------------------------------------------
# Solvers
# ----------------------------------------------------------------------


def getArcs(domains, constraints):
    """
    Return a dictionary mapping pairs (arcs) of constrained variables

    @attention: Currently unused.
    """
    arcs = {}
    for x in constraints:
        constraint, variables = x
        if len(variables) == 2:
            variable1, variable2 = variables
            arcs.setdefault(variable1, {}).setdefault(variable2, []).append(x)
            arcs.setdefault(variable2, {}).setdefault(variable1, []).append(x)
    return arcs


def doArc8(arcs, domains, assignments):
    """
    Perform the ARC-8 arc checking algorithm and prune domains

    @attention: Currently unused.
    """
    check = dict.fromkeys(domains, True)
    while check:
        variable, _ = check.popitem()
        if variable not in arcs or variable in assignments:
            continue
        domain = domains[variable]
        arcsvariable = arcs[variable]
        for othervariable in arcsvariable:
            arcconstraints = arcsvariable[othervariable]
            if othervariable in assignments:
                otherdomain = [assignments[othervariable]]
            else:
                otherdomain = domains[othervariable]
            if domain:
                # changed = False
                for value in domain[:]:
                    assignments[variable] = value
                    if otherdomain:
                        for othervalue in otherdomain:
                            assignments[othervariable] = othervalue
                            for constraint, variables in arcconstraints:
                                if not constraint(
                                    variables, domains, assignments, True
                                ):
                                    break
                            else:
                                # All constraints passed. Value is safe.
                                break
                        else:
                            # All othervalues failed. Kill value.
                            domain.hideValue(value)
                            # changed = True
                        del assignments[othervariable]
                del assignments[variable]
                # if changed:
                #     check.update(dict.fromkeys(arcsvariable))
            if not domain:
                return False
    return True


class Solver(object):
    """
    Abstract base class for solvers

    @sort: getSolution, getSolutions, getSolutionIter
    """

    def getSolution(self, domains, constraints, vconstraints):
        """
        Return one solution for the given problem

        @param domains: Dictionary mapping variables to their domains
        @type  domains: dict
        @param constraints: List of pairs of (constraint, variables)
        @type  constraints: list
        @param vconstraints: Dictionary mapping variables to a list of
                             constraints affecting the given variables.
        @type  vconstraints: dict
        """
        msg = "%s is an abstract class" % self.__class__.__name__
        raise NotImplementedError(msg)

    def getSolutions(self, domains, constraints, vconstraints):
        """
        Return all solutions for the given problem

        @param domains: Dictionary mapping variables to domains
        @type  domains: dict
        @param constraints: List of pairs of (constraint, variables)
        @type  constraints: list
        @param vconstraints: Dictionary mapping variables to a list of
                             constraints affecting the given variables.
        @type  vconstraints: dict
        """
        msg = "%s provides only a single solution" % self.__class__.__name__
        raise NotImplementedError(msg)

    def getSolutionIter(self, domains, constraints, vconstraints):
        """
        Return an iterator for the solutions of the given problem

        @param domains: Dictionary mapping variables to domains
        @type  domains: dict
        @param constraints: List of pairs of (constraint, variables)
        @type  constraints: list
        @param vconstraints: Dictionary mapping variables to a list of
                             constraints affecting the given variables.
        @type  vconstraints: dict
        """
        msg = "%s doesn't provide iteration" % self.__class__.__name__
        raise NotImplementedError(msg)


class BacktrackingSolver(Solver):
    """
    Problem solver with backtracking capabilities

    Examples:

    >>> result = [[('a', 1), ('b', 2)],
    ...           [('a', 1), ('b', 3)],
    ...           [('a', 2), ('b', 3)]]

    >>> problem = Problem(BacktrackingSolver())
    >>> problem.addVariables(["a", "b"], [1, 2, 3])
    >>> problem.addConstraint(lambda a, b: b > a, ["a", "b"])

    >>> solution = problem.getSolution()
    >>> sorted(solution.items()) in result
    True

    >>> for solution in problem.getSolutionIter():
    ...     sorted(solution.items()) in result
    True
    True
    True

    >>> for solution in problem.getSolutions():
    ...     sorted(solution.items()) in result
    True
    True
    True
    """

    def __init__(self, forwardcheck=True):
        """
        @param forwardcheck: If false forward checking will not be requested
                             to constraints while looking for solutions
                             (default is true)
        @type  forwardcheck: bool
        """
        self._forwardcheck = forwardcheck

    def getSolutionIter(self, domains, constraints, vconstraints):
        forwardcheck = self._forwardcheck
        assignments = {}

        queue = []

        while True:

            # Mix the Degree and Minimum Remaing Values (MRV) heuristics
            lst = [
                (-len(vconstraints[variable]), len(domains[variable]), variable)
                for variable in domains
            ]
            lst.sort()
            for item in lst:
                if item[-1] not in assignments:
                    # Found unassigned variable
                    variable = item[-1]
                    values = domains[variable][:]
                    if forwardcheck:
                        pushdomains = [
                            domains[x]
                            for x in domains
                            if x not in assignments and x != variable
                        ]
                    else:
                        pushdomains = None
                    break
            else:
                # No unassigned variables. We've got a solution. Go back
                # to last variable, if there's one.
                yield assignments.copy()
                if not queue:
                    return
                variable, values, pushdomains = queue.pop()
                if pushdomains:
                    for domain in pushdomains:
                        domain.popState()

            while True:
                # We have a variable. Do we have any values left?
                if not values:
                    # No. Go back to last variable, if there's one.
                    del assignments[variable]
                    while queue:
                        variable, values, pushdomains = queue.pop()
                        if pushdomains:
                            for domain in pushdomains:
                                domain.popState()
                        if values:
                            break
                        del assignments[variable]
                    else:
                        return

                # Got a value. Check it.
                assignments[variable] = values.pop()

                if pushdomains:
                    for domain in pushdomains:
                        domain.pushState()

                for constraint, variables in vconstraints[variable]:
                    if not constraint(variables, domains, assignments, pushdomains):
                        # Value is not good.
                        break
                else:
                    break

                if pushdomains:
                    for domain in pushdomains:
                        domain.popState()

            # Push state before looking for next variable.
            queue.append((variable, values, pushdomains))

        raise RuntimeError("Can't happen")

    def getSolution(self, domains, constraints, vconstraints):
        iter = self.getSolutionIter(domains, constraints, vconstraints)
        try:
            return next(iter)
        except StopIteration:
            return None

    def getSolutions(self, domains, constraints, vconstraints):
        return list(self.getSolutionIter(domains, constraints, vconstraints))


class RecursiveBacktrackingSolver(Solver):
    """
    Recursive problem solver with backtracking capabilities

    Examples:

    >>> result = [[('a', 1), ('b', 2)],
    ...           [('a', 1), ('b', 3)],
    ...           [('a', 2), ('b', 3)]]

    >>> problem = Problem(RecursiveBacktrackingSolver())
    >>> problem.addVariables(["a", "b"], [1, 2, 3])
    >>> problem.addConstraint(lambda a, b: b > a, ["a", "b"])

    >>> solution = problem.getSolution()
    >>> sorted(solution.items()) in result
    True

    >>> for solution in problem.getSolutions():
    ...     sorted(solution.items()) in result
    True
    True
    True

    >>> problem.getSolutionIter()
    Traceback (most recent call last):
       ...
    NotImplementedError: RecursiveBacktrackingSolver doesn't provide iteration
    """

    def __init__(self, forwardcheck=True):
        """
        @param forwardcheck: If false forward checking will not be requested
                             to constraints while looking for solutions
                             (default is true)
        @type  forwardcheck: bool
        """
        self._forwardcheck = forwardcheck

    def recursiveBacktracking(
        self, solutions, domains, vconstraints, assignments, single
    ):

        # Mix the Degree and Minimum Remaing Values (MRV) heuristics
        lst = [
            (-len(vconstraints[variable]), len(domains[variable]), variable)
            for variable in domains
        ]
        lst.sort()
        for item in lst:
            if item[-1] not in assignments:
                # Found an unassigned variable. Let's go.
                break
        else:
            # No unassigned variables. We've got a solution.
            solutions.append(assignments.copy())
            return solutions

        variable = item[-1]
        assignments[variable] = None

        forwardcheck = self._forwardcheck
        if forwardcheck:
            pushdomains = [domains[x] for x in domains if x not in assignments]
        else:
            pushdomains = None

        for value in domains[variable]:
            assignments[variable] = value
            if pushdomains:
                for domain in pushdomains:
                    domain.pushState()
            for constraint, variables in vconstraints[variable]:
                if not constraint(variables, domains, assignments, pushdomains):
                    # Value is not good.
                    break
            else:
                # Value is good. Recurse and get next variable.
                self.recursiveBacktracking(
                    solutions, domains, vconstraints, assignments, single
                )
                if solutions and single:
                    return solutions
            if pushdomains:
                for domain in pushdomains:
                    domain.popState()
        del assignments[variable]
        return solutions

    def getSolution(self, domains, constraints, vconstraints):
        solutions = self.recursiveBacktracking([], domains, vconstraints, {}, True)
        return solutions and solutions[0] or None

    def getSolutions(self, domains, constraints, vconstraints):
        return self.recursiveBacktracking([], domains, vconstraints, {}, False)


class LexicographicBacktrackingSolver(Solver):
    """
    Branch-and-bound solver minimizing integer linear expressions

    Expressions are minimized lexicographically: the first one has the
    highest priority, the second one is used to break ties on the first,
    and so on. At each search node the domains still available for the
    unassigned variables provide a component-wise lower bound of every
    objective. When the lower bound vector cannot improve on the best
    solution found so far, the whole subtree is pruned.

    Unlike collecting all solutions and sorting them afterwards, at most
    the incumbent solutions are kept, so the full solution set is never
    enumerated just to pick the optimum.

    Example:

    >>> problem = Problem()
    >>> problem.addVariables(["a", "b"], [1, 2, 3])
    >>> problem.addConstraint(lambda a, b: b > a, ["a", "b"])
    >>> solver = LexicographicBacktrackingSolver(
    ...     [LinearExpr({"a": 1}), LinearExpr({"b": 1})])
    >>> domains, constraints, vconstraints = problem._getArgs()
    >>> result = solver.solve(domains, constraints, vconstraints)
    >>> result.solution
    {'a': 1, 'b': 2}
    """

    def __init__(self, objectives, prune=True, forwardcheck=True):
        """
        @param objectives: Non-empty ordered sequence of L{LinearExpr}
                           objects defining the lexicographic objective
        @type  objectives: sequence of L{LinearExpr}
        @param prune: Whether to prune branches whose lower bound cannot
                      improve the incumbent (default true)
        @type  prune: bool
        @param forwardcheck: Whether forward checking should be requested
                             to constraints during the search (default true)
        @type  forwardcheck: bool
        """
        self._objectives = list(objectives)
        self._prune = prune
        self._forwardcheck = forwardcheck

    def getSolution(self, domains, constraints, vconstraints):
        result = self.solve(
            domains, constraints, vconstraints, all_solutions=False
        )
        if result.status == OptimizationResult.INFEASIBLE:
            return None
        return result.solution

    def getSolutions(self, domains, constraints, vconstraints):
        result = self.solve(
            domains, constraints, vconstraints, all_solutions=True
        )
        return result.solutions

    def getSolutionIter(self, domains, constraints, vconstraints):
        msg = "%s doesn't provide iteration" % self.__class__.__name__
        raise NotImplementedError(msg)

    def solve(
        self,
        domains,
        constraints,
        vconstraints,
        all_solutions=False,
        node_budget=None,
    ):
        """
        Run the lexicographic branch-and-bound search

        @param node_budget: Maximum number of nodes expanded (the root
                            counts as one) or None for unlimited search
        @type  node_budget: int or None
        @return: L{OptimizationResult} with status OPTIMAL, INFEASIBLE,
                 or BUDGET_EXHAUSTED
        @rtype: L{OptimizationResult}
        """
        objectives = self._objectives
        forwardcheck = self._forwardcheck
        prune = self._prune
        variables = list(domains.keys())

        state = {
            "nodes": 0,
            "budget": node_budget,
            "incumbent": None,
            "solutions": [],
            "exhausted": False,
        }
        assignments = {}

        def evaluate(solution):
            return [
                objective.value(solution) for objective in objectives
            ]

        def lower_bounds():
            return [
                objective.lower_bound(assignments, domains)
                for objective in objectives
            ]

        def cannot_improve(bounds, incumbent):
            if incumbent is None or not prune:
                return False
            if all_solutions:
                return _lex_greater(bounds, incumbent)
            return not _lex_less(bounds, incumbent)

        def remember(solution):
            values = evaluate(solution)
            incumbent = state["incumbent"]
            if incumbent is None or _lex_less(values, incumbent):
                state["incumbent"] = values
                state["solutions"] = [dict(solution)]
            elif all_solutions and values == incumbent:
                state["solutions"].append(dict(solution))

        def search():
            state["nodes"] += 1
            if (
                state["budget"] is not None
                and state["nodes"] > state["budget"]
            ):
                state["exhausted"] = True
                raise _BudgetExhausted

            unassigned = [
                variable
                for variable in variables
                if variable not in assignments
            ]
            if not unassigned:
                remember(assignments)
                return

            if cannot_improve(lower_bounds(), state["incumbent"]):
                return

            # Mix the Degree and Minimum Remaining Values (MRV) heuristics
            variable = min(
                unassigned,
                key=lambda item: (
                    -len(vconstraints[item]),
                    len(domains[item]),
                    item,
                ),
            )

            if forwardcheck:
                pushdomains = [
                    domains[item]
                    for item in variables
                    if item not in assignments and item != variable
                ]
            else:
                pushdomains = None

            for value in domains[variable][:]:
                assignments[variable] = value
                if pushdomains:
                    for domain in pushdomains:
                        domain.pushState()
                for constraint, constraint_vars in vconstraints[variable]:
                    if not constraint(
                        constraint_vars,
                        domains,
                        assignments,
                        pushdomains,
                    ):
                        break
                else:
                    search()
                if pushdomains:
                    for domain in pushdomains:
                        domain.popState()
            del assignments[variable]

        try:
            search()
        except _BudgetExhausted:
            pass

        values = state["incumbent"]
        if values is None:
            if state["exhausted"]:
                return OptimizationResult.budget_exhausted(
                    None, None, state["nodes"]
                )
            return OptimizationResult.infeasible()
        if state["exhausted"]:
            if all_solutions:
                return OptimizationResult.budget_exhausted(
                    None, list(state["solutions"]), state["nodes"], values
                )
            return OptimizationResult.budget_exhausted(
                state["solutions"][0], None, state["nodes"], values
            )
        if all_solutions:
            return OptimizationResult.optimal(
                None, list(state["solutions"]), state["nodes"], values
            )
        return OptimizationResult.optimal(
            state["solutions"][0], None, state["nodes"], values
        )


class _BudgetExhausted(Exception):
    """Internal signal used to stop the search once the budget is spent"""


def _lex_less(left, right):
    """Return True if the left vector is lexicographically smaller"""
    for left_value, right_value in zip(left, right):
        if left_value < right_value:
            return True
        if left_value > right_value:
            return False
    return False


def _lex_greater(left, right):
    """Return True if the left vector is lexicographically larger"""
    for left_value, right_value in zip(left, right):
        if left_value > right_value:
            return True
        if left_value < right_value:
            return False
    return False


class MinConflictsSolver(Solver):
    """
    Problem solver based on the minimum conflicts theory

    Examples:

    >>> result = [[('a', 1), ('b', 2)],
    ...           [('a', 1), ('b', 3)],
    ...           [('a', 2), ('b', 3)]]

    >>> problem = Problem(MinConflictsSolver())
    >>> problem.addVariables(["a", "b"], [1, 2, 3])
    >>> problem.addConstraint(lambda a, b: b > a, ["a", "b"])

    >>> solution = problem.getSolution()
    >>> sorted(solution.items()) in result
    True

    >>> problem.getSolutions()
    Traceback (most recent call last):
       ...
    NotImplementedError: MinConflictsSolver provides only a single solution

    >>> problem.getSolutionIter()
    Traceback (most recent call last):
       ...
    NotImplementedError: MinConflictsSolver doesn't provide iteration
    """

    def __init__(self, steps=1000):
        """
        @param steps: Maximum number of steps to perform before giving up
                      when looking for a solution (default is 1000)
        @type  steps: int
        """
        self._steps = steps

    def getSolution(self, domains, constraints, vconstraints):
        assignments = {}
        # Initial assignment
        for variable in domains:
            assignments[variable] = random.choice(domains[variable])
        for _ in xrange(self._steps):
            conflicted = False
            lst = list(domains.keys())
            random.shuffle(lst)
            for variable in lst:
                # Check if variable is not in conflict
                for constraint, variables in vconstraints[variable]:
                    if not constraint(variables, domains, assignments):
                        break
                else:
                    continue
                # Variable has conflicts. Find values with less conflicts.
                mincount = len(vconstraints[variable])
                minvalues = []
                for value in domains[variable]:
                    assignments[variable] = value
                    count = 0
                    for constraint, variables in vconstraints[variable]:
                        if not constraint(variables, domains, assignments):
                            count += 1
                    if count == mincount:
                        minvalues.append(value)
                    elif count < mincount:
                        mincount = count
                        del minvalues[:]
                        minvalues.append(value)
                # Pick a random one from these values.
                assignments[variable] = random.choice(minvalues)
                conflicted = True
            if not conflicted:
                return assignments
        return None


# ----------------------------------------------------------------------
# Variables
# ----------------------------------------------------------------------


class Variable(object):
    """
    Helper class for variable definition

    Using this class is optional, since any hashable object,
    including plain strings and integers, may be used as variables.
    """

    def __init__(self, name):
        """
        @param name: Generic variable name for problem-specific purposes
        @type  name: string
        """
        self.name = name

    def __repr__(self):
        return self.name


Unassigned = Variable("Unassigned")

# ----------------------------------------------------------------------
# Domains
# ----------------------------------------------------------------------


class Domain(list):
    """
    Class used to control possible values for variables

    When list or tuples are used as domains, they are automatically
    converted to an instance of that class.
    """

    def __init__(self, set):
        """
        @param set: Set of values that the given variables may assume
        @type  set: set of objects comparable by equality
        """
        list.__init__(self, set)
        self._hidden = []
        self._states = []

    def resetState(self):
        """
        Reset to the original domain state, including all possible values
        """
        self.extend(self._hidden)
        del self._hidden[:]
        del self._states[:]

    def pushState(self):
        """
        Save current domain state

        Variables hidden after that call are restored when that state
        is popped from the stack.
        """
        self._states.append(len(self))

    def popState(self):
        """
        Restore domain state from the top of the stack

        Variables hidden since the last popped state are then available
        again.
        """
        diff = self._states.pop() - len(self)
        if diff:
            self.extend(self._hidden[-diff:])
            del self._hidden[-diff:]

    def hideValue(self, value):
        """
        Hide the given value from the domain

        After that call the given value won't be seen as a possible value
        on that domain anymore. The hidden value will be restored when the
        previous saved state is popped.

        @param value: Object currently available in the domain
        """
        list.remove(self, value)
        self._hidden.append(value)


# ----------------------------------------------------------------------
# Optimization
# ----------------------------------------------------------------------


class LinearExpr(object):
    """
    Integer linear expression used as a lexicographic optimization objective

    The expression has the form C{constant + sum(coeff[var] * var)} where
    coefficients and the constant term are integers. Coefficients may be
    negative, and variables not present in the coefficient mapping simply
    do not contribute.

    Example:

    >>> overtime = LinearExpr({"a": 1, "b": -1}, constant=2)
    >>> overtime.value({"a": 3, "b": 5})
    0
    >>> overtime.lower_bound({}, {"a": Domain([1, 2]), "b": Domain([4, 5])})
    -2
    """

    def __init__(self, coefficients=None, constant=0):
        """
        @param coefficients: Mapping of variables to integer coefficients;
                             absent variables have a zero coefficient
        @type  coefficients: dict
        @param constant: Constant integer term of the expression
                         (default is zero)
        @type  constant: int
        """
        coefficients = coefficients or {}
        for variable, coefficient in coefficients.items():
            if not isinstance(coefficient, int) or isinstance(
                coefficient, bool
            ):
                raise ValueError("coefficients must be integers")
        if not isinstance(constant, int) or isinstance(constant, bool):
            raise ValueError("constant must be an integer")
        self._coefficients = dict(coefficients)
        self._constant = constant

    @property
    def coefficients(self):
        """
        Mapping of variables to their integer coefficients
        """
        return dict(self._coefficients)

    @property
    def constant(self):
        """
        Constant integer term of the expression
        """
        return self._constant

    def value(self, assignments):
        """
        Evaluate the expression for a complete assignment

        @param assignments: Mapping of variables to their values
        @type  assignments: dict
        @return: Integer value of the expression
        @rtype: int
        """
        total = self._constant
        for variable, coefficient in self._coefficients.items():
            total += assignments[variable] * coefficient
        return total

    def lower_bound(self, assignments, domains):
        """
        Return the smallest value reachable from the current domains

        Assigned variables contribute their current value, while each
        unassigned variable contributes its best domain value (the
        smallest one for a positive coefficient, the largest one for a
        negative one). Forward checking, which removes values from
        domains, therefore tightens the bound automatically.

        @param assignments: Mapping of variables assigned so far
        @type  assignments: dict
        @param domains: Mapping of variables to their current domains
        @type  domains: dict
        @return: Integer lower bound of the expression
        @rtype: int
        """
        total = self._constant
        for variable, coefficient in self._coefficients.items():
            if variable in assignments:
                total += assignments[variable] * coefficient
            else:
                domain = domains[variable]
                if coefficient >= 0:
                    total += min(domain) * coefficient
                else:
                    total += max(domain) * coefficient
        return total

    def __repr__(self):
        return "LinearExpr(%r, constant=%r)" % (
            self._coefficients,
            self._constant,
        )


class OptimizationResult(object):
    """
    Outcome of a lexicographic optimization run

    Three situations are represented by distinct statuses:

      - L{OPTIMAL}: the search completed and the returned solution or
        solutions are proved optimal;
      - L{INFEASIBLE}: the problem has no solution;
      - L{BUDGET_EXHAUSTED}: the node budget ran out. In that case
        L{solution}/L{solutions} hold the best incumbent found so far
        (possibly none), but it is explicitly not proved optimal.

    Example:

    >>> result = OptimizationResult.optimal({"a": 1}, None, 3, [0])
    >>> result.status == OptimizationResult.OPTIMAL
    True
    >>> result.is_optimal
    True
    """

    OPTIMAL = "optimal"
    INFEASIBLE = "infeasible"
    BUDGET_EXHAUSTED = "budget_exhausted"

    def __init__(
        self,
        status,
        solution=None,
        solutions=None,
        nodes=0,
        objective_values=None,
    ):
        self.status = status
        self.solution = solution
        self.solutions = solutions
        self.nodes = nodes
        self.objective_values = objective_values

    @classmethod
    def optimal(cls, solution, solutions, nodes, objective_values):
        """
        Build a result for a completed search with proved optimum
        """
        return cls(cls.OPTIMAL, solution, solutions, nodes, objective_values)

    @classmethod
    def infeasible(cls):
        """
        Build a result for a problem without any solution
        """
        return cls(cls.INFEASIBLE)

    @classmethod
    def budget_exhausted(
        cls, solution, solutions, nodes, objective_values=None
    ):
        """
        Build a result for a search stopped by the node budget

        The incumbent, if any, is the best solution found within the
        budget but is not known to be a global optimum.
        """
        return cls(
            cls.BUDGET_EXHAUSTED,
            solution,
            solutions,
            nodes,
            objective_values,
        )

    @property
    def is_optimal(self):
        """
        True if the returned solution or solutions were proved optimal
        """
        return self.status == self.OPTIMAL

    @property
    def is_infeasible(self):
        """
        True if no solution exists
        """
        return self.status == self.INFEASIBLE

    @property
    def is_budget_exhausted(self):
        """
        True if the node budget ran out before optimality was proved
        """
        return self.status == self.BUDGET_EXHAUSTED

    def __repr__(self):
        return (
            "OptimizationResult(status=%r, solution=%r, solutions=%r, "
            "nodes=%r, objective_values=%r)"
            % (
                self.status,
                self.solution,
                self.solutions,
                self.nodes,
                self.objective_values,
            )
        )


# ----------------------------------------------------------------------
# Constraints
# ----------------------------------------------------------------------


class Constraint(object):
    """
    Abstract base class for constraints
    """

    def __call__(self, variables, domains, assignments, forwardcheck=False):
        """
        Perform the constraint checking

        If the forwardcheck parameter is not false, besides telling if
        the constraint is currently broken or not, the constraint
        implementation may choose to hide values from the domains of
        unassigned variables to prevent them from being used, and thus
        prune the search space.

        @param variables: Variables affected by that constraint, in the
                          same order provided by the user
        @type  variables: sequence
        @param domains: Dictionary mapping variables to their domains
        @type  domains: dict
        @param assignments: Dictionary mapping assigned variables to their
                            current assumed value
        @type  assignments: dict
        @param forwardcheck: Boolean value stating whether forward checking
                             should be performed or not
        @return: Boolean value stating if this constraint is currently
                 broken or not
        @rtype: bool
        """
        return True

    def preProcess(self, variables, domains, constraints, vconstraints):
        """
        Preprocess variable domains

        This method is called before starting to look for solutions,
        and is used to prune domains with specific constraint logic
        when possible. For instance, any constraints with a single
        variable may be applied on all possible values and removed,
        since they may act on individual values even without further
        knowledge about other assignments.

        @param variables: Variables affected by that constraint, in the
                          same order provided by the user
        @type  variables: sequence
        @param domains: Dictionary mapping variables to their domains
        @type  domains: dict
        @param constraints: List of pairs of (constraint, variables)
        @type  constraints: list
        @param vconstraints: Dictionary mapping variables to a list of
                             constraints affecting the given variables.
        @type  vconstraints: dict
        """
        if len(variables) == 1:
            variable = variables[0]
            domain = domains[variable]
            for value in domain[:]:
                if not self(variables, domains, {variable: value}):
                    domain.remove(value)
            constraints.remove((self, variables))
            vconstraints[variable].remove((self, variables))

    def forwardCheck(self, variables, domains, assignments, _unassigned=Unassigned):
        """
        Helper method for generic forward checking

        Currently, this method acts only when there's a single
        unassigned variable.

        @param variables: Variables affected by that constraint, in the
                          same order provided by the user
        @type  variables: sequence
        @param domains: Dictionary mapping variables to their domains
        @type  domains: dict
        @param assignments: Dictionary mapping assigned variables to their
                            current assumed value
        @type  assignments: dict
        @return: Boolean value stating if this constraint is currently
                 broken or not
        @rtype: bool
        """
        unassignedvariable = _unassigned
        for variable in variables:
            if variable not in assignments:
                if unassignedvariable is _unassigned:
                    unassignedvariable = variable
                else:
                    break
        else:
            if unassignedvariable is not _unassigned:
                # Remove from the unassigned variable domain's all
                # values which break our variable's constraints.
                domain = domains[unassignedvariable]
                if domain:
                    for value in domain[:]:
                        assignments[unassignedvariable] = value
                        if not self(variables, domains, assignments):
                            domain.hideValue(value)
                    del assignments[unassignedvariable]
                if not domain:
                    return False
        return True


class FunctionConstraint(Constraint):
    """
    Constraint which wraps a function defining the constraint logic

    Examples:

    >>> problem = Problem()
    >>> problem.addVariables(["a", "b"], [1, 2])
    >>> def func(a, b):
    ...     return b > a
    >>> problem.addConstraint(func, ["a", "b"])
    >>> problem.getSolution()
    {'a': 1, 'b': 2}

    >>> problem = Problem()
    >>> problem.addVariables(["a", "b"], [1, 2])
    >>> def func(a, b):
    ...     return b > a
    >>> problem.addConstraint(FunctionConstraint(func), ["a", "b"])
    >>> problem.getSolution()
    {'a': 1, 'b': 2}
    """

    def __init__(self, func, assigned=True):
        """
        @param func: Function wrapped and queried for constraint logic
        @type  func: callable object
        @param assigned: Whether the function may receive unassigned
                         variables or not
        @type  assigned: bool
        """
        self._func = func
        self._assigned = assigned

    def __call__(
        self,
        variables,
        domains,
        assignments,
        forwardcheck=False,
        _unassigned=Unassigned,
    ):
        parms = [assignments.get(x, _unassigned) for x in variables]
        missing = parms.count(_unassigned)
        if missing:
            return (self._assigned or self._func(*parms)) and (
                not forwardcheck or
                missing != 1 or
                self.forwardCheck(variables, domains, assignments)
            )
        return self._func(*parms)


class AllDifferentConstraint(Constraint):
    """
    Constraint enforcing that values of all given variables are different

    Example:

    >>> problem = Problem()
    >>> problem.addVariables(["a", "b"], [1, 2])
    >>> problem.addConstraint(AllDifferentConstraint())
    >>> sorted(sorted(x.items()) for x in problem.getSolutions())
    [[('a', 1), ('b', 2)], [('a', 2), ('b', 1)]]
    """

    def __call__(
        self,
        variables,
        domains,
        assignments,
        forwardcheck=False,
        _unassigned=Unassigned,
    ):
        seen = {}
        for variable in variables:
            value = assignments.get(variable, _unassigned)
            if value is not _unassigned:
                if value in seen:
                    return False
                seen[value] = True
        if forwardcheck:
            for variable in variables:
                if variable not in assignments:
                    domain = domains[variable]
                    for value in seen:
                        if value in domain:
                            domain.hideValue(value)
                            if not domain:
                                return False
        return True


class AllEqualConstraint(Constraint):
    """
    Constraint enforcing that values of all given variables are equal

    Example:

    >>> problem = Problem()
    >>> problem.addVariables(["a", "b"], [1, 2])
    >>> problem.addConstraint(AllEqualConstraint())
    >>> sorted(sorted(x.items()) for x in problem.getSolutions())
    [[('a', 1), ('b', 1)], [('a', 2), ('b', 2)]]
    """

    def __call__(
        self,
        variables,
        domains,
        assignments,
        forwardcheck=False,
        _unassigned=Unassigned,
    ):
        singlevalue = _unassigned
        for variable in variables:
            value = assignments.get(variable, _unassigned)
            if singlevalue is _unassigned:
                singlevalue = value
            elif value is not _unassigned and value != singlevalue:
                return False
        if forwardcheck and singlevalue is not _unassigned:
            for variable in variables:
                if variable not in assignments:
                    domain = domains[variable]
                    if singlevalue not in domain:
                        return False
                    for value in domain[:]:
                        if value != singlevalue:
                            domain.hideValue(value)
        return True


class MaxSumConstraint(Constraint):
    """
    Constraint enforcing that values of given variables sum up to
    a given amount

    Example:

    >>> problem = Problem()
    >>> problem.addVariables(["a", "b"], [1, 2])
    >>> problem.addConstraint(MaxSumConstraint(3))
    >>> sorted(sorted(x.items()) for x in problem.getSolutions())
    [[('a', 1), ('b', 1)], [('a', 1), ('b', 2)], [('a', 2), ('b', 1)]]
    """

    def __init__(self, maxsum, multipliers=None):
        """
        @param maxsum: Value to be considered as the maximum sum
        @type  maxsum: number
        @param multipliers: If given, variable values will be multiplied by
                            the given factors before being summed to be checked
        @type  multipliers: sequence of numbers
        """
        self._maxsum = maxsum
        self._multipliers = multipliers

    def preProcess(self, variables, domains, constraints, vconstraints):
        Constraint.preProcess(self, variables, domains, constraints, vconstraints)
        multipliers = self._multipliers
        maxsum = self._maxsum
        if multipliers:
            for variable, multiplier in zip(variables, multipliers):
                domain = domains[variable]
                for value in domain[:]:
                    if value * multiplier > maxsum:
                        domain.remove(value)
        else:
            for variable in variables:
                domain = domains[variable]
                for value in domain[:]:
                    if value > maxsum:
                        domain.remove(value)

    def __call__(self, variables, domains, assignments, forwardcheck=False):
        multipliers = self._multipliers
        maxsum = self._maxsum
        sum = 0
        if multipliers:
            for variable, multiplier in zip(variables, multipliers):
                if variable in assignments:
                    sum += assignments[variable] * multiplier
            if type(sum) is float:
                sum = round(sum, 10)
            if sum > maxsum:
                return False
            if forwardcheck:
                for variable, multiplier in zip(variables, multipliers):
                    if variable not in assignments:
                        domain = domains[variable]
                        for value in domain[:]:
                            if sum + value * multiplier > maxsum:
                                domain.hideValue(value)
                        if not domain:
                            return False
        else:
            for variable in variables:
                if variable in assignments:
                    sum += assignments[variable]
            if type(sum) is float:
                sum = round(sum, 10)
            if sum > maxsum:
                return False
            if forwardcheck:
                for variable in variables:
                    if variable not in assignments:
                        domain = domains[variable]
                        for value in domain[:]:
                            if sum + value > maxsum:
                                domain.hideValue(value)
                        if not domain:
                            return False
        return True


class ExactSumConstraint(Constraint):
    """
    Constraint enforcing that values of given variables sum exactly
    to a given amount

    Example:

    >>> problem = Problem()
    >>> problem.addVariables(["a", "b"], [1, 2])
    >>> problem.addConstraint(ExactSumConstraint(3))
    >>> sorted(sorted(x.items()) for x in problem.getSolutions())
    [[('a', 1), ('b', 2)], [('a', 2), ('b', 1)]]
    """

    def __init__(self, exactsum, multipliers=None):
        """
        @param exactsum: Value to be considered as the exact sum
        @type  exactsum: number
        @param multipliers: If given, variable values will be multiplied by
                            the given factors before being summed to be checked
        @type  multipliers: sequence of numbers
        """
        self._exactsum = exactsum
        self._multipliers = multipliers

    def preProcess(self, variables, domains, constraints, vconstraints):
        Constraint.preProcess(self, variables, domains, constraints, vconstraints)
        multipliers = self._multipliers
        exactsum = self._exactsum
        if multipliers:
            for variable, multiplier in zip(variables, multipliers):
                domain = domains[variable]
                for value in domain[:]:
                    if value * multiplier > exactsum:
                        domain.remove(value)
        else:
            for variable in variables:
                domain = domains[variable]
                for value in domain[:]:
                    if value > exactsum:
                        domain.remove(value)

    def __call__(self, variables, domains, assignments, forwardcheck=False):
        multipliers = self._multipliers
        exactsum = self._exactsum
        sum = 0
        missing = False
        if multipliers:
            for variable, multiplier in zip(variables, multipliers):
                if variable in assignments:
                    sum += assignments[variable] * multiplier
                else:
                    missing = True
            if type(sum) is float:
                sum = round(sum, 10)
            if sum > exactsum:
                return False
            if forwardcheck and missing:
                for variable, multiplier in zip(variables, multipliers):
                    if variable not in assignments:
                        domain = domains[variable]
                        for value in domain[:]:
                            if sum + value * multiplier > exactsum:
                                domain.hideValue(value)
                        if not domain:
                            return False
        else:
            for variable in variables:
                if variable in assignments:
                    sum += assignments[variable]
                else:
                    missing = True
            if type(sum) is float:
                sum = round(sum, 10)
            if sum > exactsum:
                return False
            if forwardcheck and missing:
                for variable in variables:
                    if variable not in assignments:
                        domain = domains[variable]
                        for value in domain[:]:
                            if sum + value > exactsum:
                                domain.hideValue(value)
                        if not domain:
                            return False
        if missing:
            return sum <= exactsum
        else:
            return sum == exactsum


class MinSumConstraint(Constraint):
    """
    Constraint enforcing that values of given variables sum at least
    to a given amount

    Example:

    >>> problem = Problem()
    >>> problem.addVariables(["a", "b"], [1, 2])
    >>> problem.addConstraint(MinSumConstraint(3))
    >>> sorted(sorted(x.items()) for x in problem.getSolutions())
    [[('a', 1), ('b', 2)], [('a', 2), ('b', 1)], [('a', 2), ('b', 2)]]
    """

    def __init__(self, minsum, multipliers=None):
        """
        @param minsum: Value to be considered as the minimum sum
        @type  minsum: number
        @param multipliers: If given, variable values will be multiplied by
                            the given factors before being summed to be checked
        @type  multipliers: sequence of numbers
        """
        self._minsum = minsum
        self._multipliers = multipliers

    def __call__(self, variables, domains, assignments, forwardcheck=False):
        for variable in variables:
            if variable not in assignments:
                return True
        else:
            multipliers = self._multipliers
            minsum = self._minsum
            sum = 0
            if multipliers:
                for variable, multiplier in zip(variables, multipliers):
                    sum += assignments[variable] * multiplier
            else:
                for variable in variables:
                    sum += assignments[variable]
            if type(sum) is float:
                sum = round(sum, 10)
            return sum >= minsum


class InSetConstraint(Constraint):
    """
    Constraint enforcing that values of given variables are present in
    the given set

    Example:

    >>> problem = Problem()
    >>> problem.addVariables(["a", "b"], [1, 2])
    >>> problem.addConstraint(InSetConstraint([1]))
    >>> sorted(sorted(x.items()) for x in problem.getSolutions())
    [[('a', 1), ('b', 1)]]
    """

    def __init__(self, set):
        """
        @param set: Set of allowed values
        @type  set: set
        """
        self._set = set

    def __call__(self, variables, domains, assignments, forwardcheck=False):
        # preProcess() will remove it.
        raise RuntimeError("Can't happen")

    def preProcess(self, variables, domains, constraints, vconstraints):
        set = self._set
        for variable in variables:
            domain = domains[variable]
            for value in domain[:]:
                if value not in set:
                    domain.remove(value)
            vconstraints[variable].remove((self, variables))
        constraints.remove((self, variables))


class NotInSetConstraint(Constraint):
    """
    Constraint enforcing that values of given variables are not present in
    the given set

    Example:

    >>> problem = Problem()
    >>> problem.addVariables(["a", "b"], [1, 2])
    >>> problem.addConstraint(NotInSetConstraint([1]))
    >>> sorted(sorted(x.items()) for x in problem.getSolutions())
    [[('a', 2), ('b', 2)]]
    """

    def __init__(self, set):
        """
        @param set: Set of disallowed values
        @type  set: set
        """
        self._set = set

    def __call__(self, variables, domains, assignments, forwardcheck=False):
        # preProcess() will remove it.
        raise RuntimeError("Can't happen")

    def preProcess(self, variables, domains, constraints, vconstraints):
        set = self._set
        for variable in variables:
            domain = domains[variable]
            for value in domain[:]:
                if value in set:
                    domain.remove(value)
            vconstraints[variable].remove((self, variables))
        constraints.remove((self, variables))


class SomeInSetConstraint(Constraint):
    """
    Constraint enforcing that at least some of the values of given
    variables must be present in a given set

    Example:

    >>> problem = Problem()
    >>> problem.addVariables(["a", "b"], [1, 2])
    >>> problem.addConstraint(SomeInSetConstraint([1]))
    >>> sorted(sorted(x.items()) for x in problem.getSolutions())
    [[('a', 1), ('b', 1)], [('a', 1), ('b', 2)], [('a', 2), ('b', 1)]]
    """

    def __init__(self, set, n=1, exact=False):
        """
        @param set: Set of values to be checked
        @type  set: set
        @param n: Minimum number of assigned values that should be present
                  in set (default is 1)
        @type  n: int
        @param exact: Whether the number of assigned values which are
                      present in set must be exactly C{n}
        @type  exact: bool
        """
        self._set = set
        self._n = n
        self._exact = exact

    def __call__(self, variables, domains, assignments, forwardcheck=False):
        set = self._set
        missing = 0
        found = 0
        for variable in variables:
            if variable in assignments:
                found += assignments[variable] in set
            else:
                missing += 1
        if missing:
            if self._exact:
                if not (found <= self._n <= missing + found):
                    return False
            else:
                if self._n > missing + found:
                    return False
            if forwardcheck and self._n - found == missing:
                # All unassigned variables must be assigned to
                # values in the set.
                for variable in variables:
                    if variable not in assignments:
                        domain = domains[variable]
                        for value in domain[:]:
                            if value not in set:
                                domain.hideValue(value)
                        if not domain:
                            return False
        else:
            if self._exact:
                if found != self._n:
                    return False
            else:
                if found < self._n:
                    return False
        return True


class SomeNotInSetConstraint(Constraint):
    """
    Constraint enforcing that at least some of the values of given
    variables must not be present in a given set

    Example:

    >>> problem = Problem()
    >>> problem.addVariables(["a", "b"], [1, 2])
    >>> problem.addConstraint(SomeNotInSetConstraint([1]))
    >>> sorted(sorted(x.items()) for x in problem.getSolutions())
    [[('a', 1), ('b', 2)], [('a', 2), ('b', 1)], [('a', 2), ('b', 2)]]
    """

    def __init__(self, set, n=1, exact=False):
        """
        @param set: Set of values to be checked
        @type  set: set
        @param n: Minimum number of assigned values that should not be present
                  in set (default is 1)
        @type  n: int
        @param exact: Whether the number of assigned values which are
                      not present in set must be exactly C{n}
        @type  exact: bool
        """
        self._set = set
        self._n = n
        self._exact = exact

    def __call__(self, variables, domains, assignments, forwardcheck=False):
        set = self._set
        missing = 0
        found = 0
        for variable in variables:
            if variable in assignments:
                found += assignments[variable] not in set
            else:
                missing += 1
        if missing:
            if self._exact:
                if not (found <= self._n <= missing + found):
                    return False
            else:
                if self._n > missing + found:
                    return False
            if forwardcheck and self._n - found == missing:
                # All unassigned variables must be assigned to
                # values not in the set.
                for variable in variables:
                    if variable not in assignments:
                        domain = domains[variable]
                        for value in domain[:]:
                            if value in set:
                                domain.hideValue(value)
                        if not domain:
                            return False
        else:
            if self._exact:
                if found != self._n:
                    return False
            else:
                if found < self._n:
                    return False
        return True


if __name__ == "__main__":
    import doctest

    doctest.testmod()
