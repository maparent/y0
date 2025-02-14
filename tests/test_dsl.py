# -*- coding: utf-8 -*-

"""Test the probability DSL."""

import itertools as itt
import unittest

from y0.dsl import (
    A, B, C, ConditionalProbability, CounterfactualVariable, D, Fraction, Intervention, JointProbability, P, Q, S, Sum,
    T, Variable, W, X, Y, Z,
)

V = Variable('V')


class TestDSL(unittest.TestCase):
    """Tests for the stringifying instances of the probability DSL."""

    def assert_text(self, s: str, expression):
        """Assert the expression when it is converted to a string."""
        self.assertIsInstance(s, str)
        self.assertEqual(s, expression.to_text())

    def test_variable(self):
        """Test the variable DSL object."""
        self.assert_text('A', Variable('A'))
        self.assert_text('A', A)  # shorthand for testing purposes

    def test_intervention(self):
        """Test the invervention DSL object."""
        self.assert_text('W*', Intervention('W', True))
        self.assert_text('W', Intervention('W', False))
        self.assert_text('W', Intervention('W'))  # False is the default
        self.assert_text('W', W)  # shorthand for testing purposes

        # inversions using the unary ~ operator
        self.assert_text('W', ~Intervention('W', True))
        self.assert_text('W*', ~Intervention('W', False))  # False is still the default
        self.assert_text('W*', ~Intervention('W'))
        self.assert_text('W*', ~W)

    def test_counterfactual_variable(self):
        """Test the Counterfactual Variable DSL object."""
        # Normal instantiation
        self.assert_text('Y_{W}', CounterfactualVariable('Y', [W]))
        self.assert_text('Y_{W*}', CounterfactualVariable('Y', [~W]))

        # Instantiation with list-based operand to matmul @ operator
        self.assert_text('Y_{W}', Variable('Y') @ [W])
        self.assert_text('Y_{W}', Y @ [W])
        self.assert_text('Y_{W*}', Variable('Y') @ [~W])
        self.assert_text('Y_{W*}', Y @ [~W])

        # Instantiation with two variables
        self.assert_text('Y_{X,W*}', CounterfactualVariable('Y', [Intervention('X'), ~Intervention('W')]))

        # Instantiation with matmul @ operator and single operand
        self.assert_text('Y_{W}', Y @ Intervention('W'))
        self.assert_text('Y_{W*}', Y @ ~Intervention('W'))

        # Instantiation with matmul @ operator and list operand
        self.assert_text('Y_{X,W*}', Y @ [X, ~W])

        # Instantiation with matmul @ operator (chained)
        self.assert_text('Y_{X,W*}', Y @ X @ ~W)

    def test_counterfactual_errors(self):
        """Test that if two variables with the same name are given, an error is raised, regardless of star state."""
        for a, b in itt.product([True, False], [True, False]):
            with self.subTest(a=a, b=b), self.assertRaises(ValueError):
                Y @ Intervention('X', star=a) @ Intervention('X', star=b)

    def test_conditional(self):
        """Test the ConditionalProbability DSL object."""
        # Normal instantiation
        self.assert_text('A|B', ConditionalProbability(A, [B]))

        # Instantiation with list-based operand to or | operator
        self.assert_text('A|B', Variable('A') | [B])
        self.assert_text('A|B', A | [B])

        # # Instantiation with two variables
        self.assert_text('A|B,C', A | [B, C])

        # Instantiation with or | operator and single operand
        self.assert_text('A|B', Variable('A') | B)
        self.assert_text('A|B', A | B)

        # Instantiation with or | operator (chained)
        self.assert_text('A|B,C', A | B | C)

        # Counterfactual uses work basically the same.
        #  Note: @ binds more tightly than |, but it's probably better to use parentheses
        self.assert_text('Y_{W}|B', (Y @ W) | B)
        self.assert_text('Y_{W}|B', Y @ W | B)
        self.assert_text('Y_{W}|B,C', Y @ W | B | C)
        self.assert_text('Y_{W,X*}|B,C', Y @ W @ ~X | B | C)
        self.assert_text('Y_{W,X*}|B_{Q*},C', Y @ W @ ~X | B @ Intervention('Q', True) | C)

    def test_conditional_probability(self):
        """Test generation of conditional probabilities."""
        self.assert_text('P(A|B)', P(ConditionalProbability(A, [B])))
        self.assert_text('P(A|B)', P(A | [B]))
        self.assert_text('P(A|B,C)', P(ConditionalProbability(A, [B]) | C))
        self.assert_text('P(A|B,C)', P(A | [B, C]))
        self.assert_text('P(A|B,C)', P(A | B | C))

    def test_joint(self):
        """Test the JointProbability DSL object."""
        self.assert_text('A,B', JointProbability([A, B]))
        self.assert_text('A,B', A & B)
        self.assert_text('A,B,C', JointProbability([A, B, C]))
        self.assert_text('A,B,C', A & B & C)

    def test_joint_probability(self):
        """Test generation of joint probabilities."""
        # Shortcut for list building
        self.assert_text('P(A,B)', P([A, B]))
        self.assert_text('P(A,B)', P(A, B))
        self.assert_text('P(A,B)', P(A & B))
        self.assert_text('P(A,B,C)', P(A & B & C))

    def test_sum(self):
        """Test the Sum DSL object."""
        # Sum with no variables
        self.assert_text(
            "[ sum_{} P(A|B) P(C|D) ]",
            Sum(P(A | B) * P(C | D)),
        )
        # Sum with one variable
        self.assert_text(
            "[ sum_{S} P(A|B) P(C|D) ]",
            Sum(P(A | B) * P(C | D), [S]),
        )
        # Sum with two variables
        self.assert_text(
            "[ sum_{S,T} P(A|B) P(C|D) ]",
            Sum(P(A | B) * P(C | D), [S, T]),
        )

        # CRAZY sum syntax! pycharm doesn't like this usage of __class_getitem__ though so idk if we'll keep this
        self.assert_text(
            "[ sum_{S} P(A|B) P(C|D) ]",
            Sum[S](P(A | B) * P(C | D)),
        )
        self.assert_text(
            "[ sum_{S,T} P(A|B) P(C|D) ]",
            Sum[S, T](P(A | B) * P(C | D)),
        )

        # Sum with sum inside
        self.assert_text(
            "[ sum_{S,T} P(A|B) [ sum_{Q} P(C|D) ] ]",
            Sum(P(A | B) * Sum(P(C | D), [Q]), [S, T]),
        )

    def test_jeremy(self):
        """Test assorted complicated objects from Jeremy."""
        self.assert_text(
            '[ sum_{W} P(Y_{Z*,W},X) P(D) P(Z_{D}) P(W_{X*}) ]',
            Sum(P((Y @ ~Z @ W) & X) * P(D) * P(Z @ D) * P(W @ ~X), [W]),
        )

        self.assert_text(
            '[ sum_{W} P(Y_{Z*,W},X) P(W_{X*}) ]',
            Sum(P(Y @ ~Z @ W & X) * P(W @ ~X), [W]),
        )

        self.assert_text(
            'frac_{[ sum_{W} P(Y_{Z,W},X) P(W_{X*}) ]}{[ sum_{Y} [ sum_{W} P(Y_{Z,W},X) P(W_{X*}) ] ]}',
            Fraction(
                Sum(P(Y @ Z @ W & X) * P(W @ ~X), [W]),
                Sum(Sum(P(Y @ Z @ W & X) * P(W @ ~X), [W]), [Y]),
            ),
        )

        self.assert_text(
            '[ sum_{D} P(Y_{Z*,W},X) P(D) P(Z_{D}) P(W_{X*}) ]',
            Sum(P(Y @ ~Z @ W & X) * P(D) * P(Z @ D) * P(W @ ~X), [D]),
        )

        self.assert_text(
            '[ sum_{W,D,Z,V} [ sum_{} P(W|X) ] [ sum_{} [ sum_{X,W,Z,Y,V} P(X,W,D,Z,Y,V) ] ]'
            ' [ sum_{} P(Z|D,V) ] [ sum_{} [ sum_{X} P(Y|X,D,V,Z,W) P(X) ] ]'
            ' [ sum_{} [ sum_{X,W,D,Z,Y} P(X,W,D,Z,Y,V) ] ] ]',
            Sum[W, D, Z, V](
                Sum(P(W | X))
                * Sum(Sum[X, W, Z, Y, V](P(X, W, D, Z, Y, V)))
                * Sum(P(Z | [D, V]))
                * Sum(Sum[X](P(Y | [X, D, V, Z, W]) * P(X)))
                * Sum(Sum[X, W, D, Z, Y](P(X, W, D, Z, Y, V))),
            ),
        )

        '''
        [[sum_{D,Z,V} [sum_{} [sum_{X,W,Z,Y,V} P(X,W,D,Z,Y,V)]][sum_{}P(Z|D,V)][sum_{} [sum_{X} P(Y|X,D,V,Z,W)P(X|)]]
        [sum_{} [sum_{X,W,D,Z,Y} P(X,W,D,Z,Y,V)]]]]/[ sum_{Y}[sum_{D,Z,V} [sum_{} [sum_{X,W,Z,Y,V} P(X,W,D,Z,Y,V)]]
        [sum_{}P(Z|D,V)][sum_{} [sum_{X} P(Y|X,D,V,Z,W)P(X|)]][sum_{} [sum_{X,W,D,Z,Y} P(X,W,D,Z,Y,V)]]]]
        '''
