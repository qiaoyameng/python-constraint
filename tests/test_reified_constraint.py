from itertools import product

from constraint import (
    AllDifferentConstraint,
    AllEqualConstraint,
    Domain,
    ExactSumConstraint,
    FunctionConstraint,
    MinSumConstraint,
    Problem,
    ReifiedConstraint,
    Unassigned,
)


def build_problem(flag_domain=(False, True)):
    problem = Problem()
    problem.addVariable("amount", range(1, 6))
    problem.addVariable("code", [1, 2])
    problem.addVariable("customer", [0, 1])
    problem.addVariable("premium", [0, 1])
    problem.addVariable("b1", flag_domain)
    problem.addVariable("b2", flag_domain)
    problem.addVariable("b3", flag_domain)
    problem.addVariable("eligible", flag_domain)
    problem.addVariable("discount", [0, 10])

    problem.addConstraint(
        ReifiedConstraint(
            "b1",
            FunctionConstraint(lambda amount, code: amount >= 3 and code == 1),
        ),
        ["amount", "code"],
    )
    problem.addConstraint(
        ReifiedConstraint("b2", MinSumConstraint(3)), ["amount", "customer"]
    )
    problem.addConstraint(
        ReifiedConstraint("b3", AllDifferentConstraint()), ["code", "premium"]
    )
    problem.addConstraint(
        ReifiedConstraint("eligible", ExactSumConstraint(1)),
        ["b1", "b2", "b3"],
    )
    problem.addConstraint(
        lambda eligible, discount: discount == (10 if eligible else 0),
        ["eligible", "discount"],
    )
    return problem


def brute_force_discount_solutions():
    solutions = []
    domains = [range(1, 6), [1, 2], [0, 1], [0, 1]]
    for amount, code, customer, premium in product(*domains):
        b1 = amount >= 3 and code == 1
        b2 = amount + customer >= 3
        b3 = code != premium
        eligible = sum((b1, b2, b3)) == 1
        discount = 10 if eligible else 0
        solutions.append(
            {
                "amount": amount,
                "code": code,
                "customer": customer,
                "premium": premium,
                "b1": b1,
                "b2": b2,
                "b3": b3,
                "eligible": eligible,
                "discount": discount,
            }
        )
    return solutions


def test_conditional_discount_solutions_match_brute_force():
    solutions = build_problem().getSolutions()
    expected = brute_force_discount_solutions()

    assert len(solutions) == len(expected)
    assert {tuple(sorted(solution.items())) for solution in solutions} == {
        tuple(sorted(solution.items())) for solution in expected
    }


def test_equality_reification_uses_global_negation():
    problem = Problem()
    problem.addVariables(["a", "b", "c"], [1, 2])
    problem.addVariable("same", [False, True])
    problem.addConstraint(
        ReifiedConstraint("same", AllEqualConstraint()), ["a", "b", "c"]
    )

    assert sorted(
        (
            solution["a"],
            solution["b"],
            solution["c"],
            solution["same"],
        )
        for solution in problem.getSolutions()
    ) == [
        (1, 1, 1, True),
        (1, 1, 2, False),
        (1, 2, 1, False),
        (1, 2, 2, False),
        (2, 1, 1, False),
        (2, 1, 2, False),
        (2, 2, 1, False),
        (2, 2, 2, True),
    ]


def test_partial_assignment_keeps_both_possibilities():
    reified = ReifiedConstraint("flag", AllDifferentConstraint())
    variables = ["a", "b"]
    domains = {
        "a": Domain([1, 2]),
        "b": Domain([1, 2]),
        "flag": Domain([False, True]),
    }

    assert reified(variables, domains, {}, True)
    assert list(domains["flag"]) == [False, True]

    domains["b"].pushState()
    domains["flag"].pushState()
    assert reified(variables, domains, {"a": 1}, True)
    assert list(domains["flag"]) == [False, True]
    assert list(domains["b"]) == [1, 2]

    assert reified(variables, domains, {"a": 1, "b": 1}, True)
    assert list(domains["flag"]) == [False]


def test_function_relation_only_receives_complete_assignments():
    seen = []

    def relation(a, b):
        assert a is not Unassigned
        assert b is not Unassigned
        seen.append((a, b))
        return a < b

    problem = Problem()
    problem.addVariables(["a", "b"], [1, 2])
    problem.addVariable("flag", [False, True])
    problem.addConstraint(ReifiedConstraint("flag", relation), ["a", "b"])

    solutions = problem.getSolutions()

    assert seen
    assert {
        (solution["a"], solution["b"], solution["flag"])
        for solution in solutions
    } == {(1, 1, False), (1, 2, True), (2, 1, False), (2, 2, False)}


def test_fixed_boolean_branches_prune_different_values():
    true_problem = Problem()
    true_problem.addVariable("a", [1, 2, 3])
    true_problem.addVariable("flag", [True])
    true_problem.addConstraint(
        ReifiedConstraint("flag", ExactSumConstraint(1)), ["a"]
    )

    false_problem = Problem()
    false_problem.addVariable("a", [1, 2, 3])
    false_problem.addVariable("flag", [False])
    false_problem.addConstraint(
        ReifiedConstraint("flag", ExactSumConstraint(1)), ["a"]
    )

    true_domains, _, _ = true_problem._getArgs()
    false_domains, _, _ = false_problem._getArgs()

    assert list(true_domains["a"]) == [1]
    assert list(false_domains["a"]) == [2, 3]
