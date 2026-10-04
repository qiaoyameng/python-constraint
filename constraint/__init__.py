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
                MinConflictsSolver
@group Constraints: Constraint,
                    FunctionConstraint,
                    AllDifferentConstraint,
                    AllDifferentMatchingConstraint,
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
from .compat import xrange

__all__ = [
    "Problem",
    "Variable",
    "Domain",
    "Unassigned",
    "Solver",
    "BacktrackingSolver",
    "RecursiveBacktrackingSolver",
    "MinConflictsSolver",
    "Constraint",
    "FunctionConstraint",
    "AllDifferentConstraint",
    "AllDifferentMatchingConstraint",
    "AllEqualConstraint",
    "MaxSumConstraint",
    "ExactSumConstraint",
    "MinSumConstraint",
    "InSetConstraint",
    "NotInSetConstraint",
    "SomeInSetConstraint",
    "SomeNotInSetConstraint",
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


def _strongly_connected_components(nodes, successors):
    """
    Tarjan's algorithm (iterative) for strongly connected components

    @param nodes: Iterable of graph nodes
    @param successors: Callable mapping a node to its outgoing edges
    @return: Dictionary mapping each node to its component representative
    @rtype: dict
    """
    index = {}
    lowlink = {}
    component = {}
    stack = []
    on_stack = set()
    counter = 0
    for root in nodes:
        if root in index:
            continue
        index[root] = lowlink[root] = counter
        counter += 1
        stack.append(root)
        on_stack.add(root)
        work = [(root, iter(successors(root)))]
        while work:
            node, iterator = work[-1]
            for nxt in iterator:
                if nxt not in index:
                    index[nxt] = lowlink[nxt] = counter
                    counter += 1
                    stack.append(nxt)
                    on_stack.add(nxt)
                    work.append((nxt, iter(successors(nxt))))
                    break
                elif nxt in on_stack and index[nxt] < lowlink[node]:
                    lowlink[node] = index[nxt]
            else:
                work.pop()
                if work:
                    parent = work[-1][0]
                    if lowlink[node] < lowlink[parent]:
                        lowlink[parent] = lowlink[node]
                if lowlink[node] == index[node]:
                    while True:
                        member = stack.pop()
                        on_stack.discard(member)
                        component[member] = node
                        if member == node:
                            break
    return component


def _matching_support(variables, domains, assignments):
    """
    Compute values taking part in at least one complete matching

    Builds the bipartite support graph between the given variables and
    their candidate values (assigned variables contribute their current
    value as a singleton), finds a maximum matching, and then determines
    which edges belong to some maximum matching: matched edges, edges on
    an alternating path starting at a free value, and edges on an
    alternating cycle (Régin's filtering for AllDifferent).

    @param variables: Variables affected by the constraint
    @type  variables: sequence
    @param domains: Dictionary mapping variables to their domains
    @type  domains: dict
    @param assignments: Dictionary with the current variable assignments
    @type  assignments: dict
    @return: Dictionary mapping each variable to the set of its supported
             values, or None if no matching covers all variables
    @rtype: dict or None
    """
    neighbors = {}
    value_to_variables = {}
    for variable in variables:
        if variable in assignments:
            candidates = (assignments[variable],)
        else:
            candidates = domains[variable]
        neighbors[variable] = list(candidates)
        for value in candidates:
            value_to_variables.setdefault(value, []).append(variable)

    # Maximum bipartite matching via augmenting paths (Kuhn's algorithm).
    match_variable = {}
    match_value = {}

    def augment(variable, seen):
        for value in neighbors[variable]:
            if value not in seen:
                seen.add(value)
                if value not in match_value or augment(match_value[value], seen):
                    match_variable[variable] = value
                    match_value[value] = variable
                    return True
        return False

    for variable in variables:
        augment(variable, set())
    if len(match_variable) < len(variables):
        return None

    # Directed matching graph: matched edges go from variable nodes to
    # value nodes, unmatched edges from value nodes to variable nodes.
    # Nodes are tagged so that variables and values never collide.
    def successors(node):
        kind, obj = node
        if kind == 0:
            return ((1, match_variable[obj]),)
        return tuple(
            (0, variable)
            for variable in value_to_variables[obj]
            if match_variable[variable] != obj
        )

    # Edges on an alternating path starting at a free (unmatched) value.
    reachable = set()
    queue = [
        (1, value) for value in value_to_variables if value not in match_value
    ]
    while queue:
        node = queue.pop()
        if node in reachable:
            continue
        reachable.add(node)
        queue.extend(successors(node))

    # Edges on an alternating cycle link nodes of the same component.
    nodes = [(0, variable) for variable in variables]
    nodes.extend((1, value) for value in value_to_variables)
    component = _strongly_connected_components(nodes, successors)

    support = {}
    for variable in variables:
        node = (0, variable)
        matched = match_variable[variable]
        keep = set()
        for value in neighbors[variable]:
            if (
                value == matched
                or (1, value) in reachable
                or component[(1, value)] == component[node]
            ):
                keep.add(value)
        support[variable] = keep
    return support


class AllDifferentMatchingConstraint(Constraint):
    """
    Constraint enforcing that values of all given variables are different,
    propagating through bipartite matching

    Unlike L{AllDifferentConstraint}, which only reacts to values already
    assigned, this constraint builds the variable/value support graph on
    every check, computes a maximum matching, and removes candidate values
    that cannot take part in any complete matching. Hall-set conflicts
    (more variables than distinct candidate values in some subset) are
    therefore detected before variables are assigned, and infeasible
    branches are pruned as soon as domain changes make them apparent.

    A value is only removed when it belongs to no maximum matching at
    all; simply not being used by the particular matching that was found
    is never a reason for removal. All pruning done while searching goes
    through the domain state stack, so it is undone when the search
    backtracks and never leaks into sibling branches.

    Example:

    >>> problem = Problem()
    >>> problem.addVariables(["shift1", "shift2", "shift3"], ["ann", "bob"])
    >>> problem.addConstraint(AllDifferentMatchingConstraint())
    >>> problem.getSolution() is None
    True

    >>> problem = Problem()
    >>> problem.addVariable("a", [1, 2])
    >>> problem.addVariable("b", [1, 2])
    >>> problem.addVariable("c", [1, 2, 3])
    >>> problem.addConstraint(AllDifferentMatchingConstraint())
    >>> sorted(sorted(x.items()) for x in problem.getSolutions())
    [[('a', 1), ('b', 2), ('c', 3)], [('a', 2), ('b', 1), ('c', 3)]]
    """

    def __call__(self, variables, domains, assignments, forwardcheck=False):
        support = _matching_support(variables, domains, assignments)
        if support is None:
            return False
        if forwardcheck:
            for variable in variables:
                if variable not in assignments:
                    domain = domains[variable]
                    keep = support[variable]
                    for value in domain[:]:
                        if value not in keep:
                            domain.hideValue(value)
                    if not domain:
                        return False
        return True

    def preProcess(self, variables, domains, constraints, vconstraints):
        support = _matching_support(variables, domains, {})
        if support is None:
            # No matching covers all variables: the constraint can never
            # be satisfied, so report an empty domain before searching.
            del domains[variables[0]][:]
            return
        for variable in variables:
            domain = domains[variable]
            keep = support[variable]
            for value in domain[:]:
                if value not in keep:
                    domain.remove(value)


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
