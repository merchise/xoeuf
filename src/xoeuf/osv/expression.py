#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Copyright (c) Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can do what the LICENCE file allows you to.
#
"""Extensions to `odoo.osv.expression`.

This module reexport all symbols from the `odoo.osv.expression` so it can be
used a replacement.

Additions and changes:

- There's a new `Domain`:class: which allows to do some arithmetic with
  domains.

- The functions `AND`:func: and `OR`:func: don't need to you pass a domain in
  first normal form, they ensure that themselves.

- You can test some a weak form of implication, i.e ``Domain(X).implies(Y)``
  is True if we can proof that whenever ``X`` is True, ``Y`` also is.  This
  method can have false negatives, but not false positives: there are cases
  for which we can't find the proof (we return False) which should be True;
  but if we return True, there's a proof.

"""

import operator
from itertools import chain

from odoo.osv import expression as _odoo_expression
from xotl.tools.deprecation import deprecated

# TODO: `copy_members` is deprecated since xotl.tools 1.8, use instead the same
# mechanisms as `xotl.tools.future`.
from xotl.tools.modules import copy_members as _copy_python_module_members
from xotl.tools.objects import classproperty

from xoeuf.osv import ql
from xoeuf.utils import crossmethod

this = _copy_python_module_members(_odoo_expression)
del _copy_python_module_members
del _odoo_expression

# This import is needed to avoid shadowing of 'datetime.datetime' repr in filter's AST.
# Otherwise domains like the one in test_regression_asfilter_with_datetime fail, because
# odoo.osv.expression does 'from datetime import datetime'
import datetime  # noqa

UNARY_OPERATORS = [this.NOT_OPERATOR]
BINARY_OPERATORS = [this.AND_OPERATOR, this.OR_OPERATOR]
KIND_OPERATOR = "OPERATOR"
KIND_TERM = "TERM"


# Exports normalize_leaf so that we can replace 'from odoo.
def normalize_leaf(term):
    if this.is_leaf(term):
        left, operator, right = this.normalize_leaf(term)
        # Avoid no hashable values in domain terms
        if not getattr(right, "__hash__", False) and hasattr(right, "__iter__"):  # noqa
            right = tuple(right)
        return left, operator, right
    return term


class Domain(list):
    """A predicate expressed as an Odoo domain.

    .. note:: This is an *operational* wrapper around normal Odoo domains
              (lists) with methods to do logical manipulation of such values.

    It's a subtype of Odoo domains (i.e `list`:class:), which means that
    wherever an Odoo domain is expected you can use a Domain.  See the `Liskov
    substitution principle`__.

    __ https://en.wikipedia.org/wiki/Liskov_substitution_principle

    """

    def __init__(self, seq=None):
        # TODO: Can you do some sanity check to avoid common mistakes?  For
        # me, it's normal that I do ``Model.search(['field', '=', value])``
        # and forget the tuple...
        from odoo.tools.safe_eval import const_eval

        seq = seq or ()
        # some times the domains are saved in db in char or text fields.
        if isinstance(seq, str):
            seq = const_eval(seq)
        super(Domain, self).__init__(seq)

    def implies(self, other):
        """Check if a domain implies another.

        For any two domains `A` and `B`, the following rules are always true:

        - ``A.implies(A)``
        - ``(A & B).implies(A)``
        - ``A.implies(A | B)``.
        - ``not B.implies(A) == (A | B).implies(A)``

        """
        other = DomainTree(Domain(other).second_normal_form)
        return DomainTree(self.second_normal_form).implies(other)

    @classproperty
    def TRUE(cls):
        "The domain which is True.  Implemented as ``[(1, '=', 1)]``."
        return cls(this.TRUE_DOMAIN)

    @classproperty
    def FALSE(cls):
        "The domain which is False.  Implemented as ``[(0, '=', 1)]``."
        return cls(this.FALSE_DOMAIN)

    @property
    def first_normal_form(self):
        """The first normal form.

        The first normal form is the same domain with all `and` operators
        explicit.

        For instance, having ``domain`` value like::

            >>> domain = Domain(
            ...     [('field_y', 'not in', False), ('field_x', '!=', 'value')]
            ... )

        Then::

            >>> domain.first_normal_form
            ['&', ('field_y', 'not in', False), ('field_x', '!=', 'value')]

        """
        return Domain(this.normalize_domain(self))

    @property
    def second_normal_form(self):
        """The second normal form.

        After obtaining the `first_normal_from`:attr:, change terms to its
        canonical form, and distribute the `not` logical operator inside
        terms.

        .. seealso:: `normalize_leaf`:func: for the canonical form of terms.

        .. seealso:: `distribute_not`:meth:

        Example::

            >>> domain1 = Domain([
            ...     ('field_x', 'not in', False),
            ...     '!',
            ...     ('field_y', '>', 1)
            ... ])

            >>> domain2 = Domain([
            ...     '|',
            ...     ('field_x', 'not in', False),
            ...     ('field_y', '<>', 'value'),
            ...     ('field_z', '>', 1)
            ... ])

            >>> domain3 = Domain([
            ...     '|',
            ...     ('field_x', 'not in', False),
            ...     '!',
            ...     ('field_y', '<>', 'value'),
            ...     ('field_z', '>', 1)
            ... ])

            >>> domain1.first_normal_form
            ['&', ('field_x', '!=', False), ('field_y', '<=', 1)]

            >>> domain2.first_normal_form
            [
                '&',
                '|',
                ('field_x', '!=', False),
                ('field_y', '!=', 'value'),
                ('field_z', '>', 1)
            ]

            >>> domain3.first_normal_form
            [
                '&',
                '|',
                ('field_x', '!=', False),
                ('field_y', '=', 'value'),
                ('field_z', '>', 1)
            ]

        """
        res = self.first_normal_form
        res = Domain((normalize_leaf(item) for item in res))
        return res.distribute_not()

    @property
    def simplified(self):
        """A simplified second normal form of the domain.

        Examples:

            >>> domain1 = Domain([
            ...     ('field_x', '!=', False),
            ...     ('field_y', '=', 'value'),
            ...     ('field_z', 'in', (1, 2, 3)),
            ...     ('field_y', '=', 'value'),
            ... ])
            >>> domain1.simplified
            [
                '&',
                '&',
                ('field_x', '!=', False),
                ('field_y', '=', 'value'),
                ('field_z', 'in', (1, 2, 3))
            ]

            >>> domain2 = Domain([
            ...     '|',
            ...     ('field_x', '!=', False),
            ...     ('field_y', '=', 'value'),
            ...     ('field_z', 'in', (1, 2, 3)),
            ...     '|',
            ...     ('field_y', '=', 'value'),
            ...     ('field_x', '!=', False)
            ... ])
            >>> domain2.simplified
            [
                '&',
                '|',
                ('field_x', '!=', False),
                ('field_y', '=', 'value'),
                ('field_z', 'in', (1, 2, 3))
            ]

            >>> domain3 = Domain([
            ...     ('field_y', '!=', False),
            ...     ('field_x', 'in', (1,)),
            ...     '|',
            ...     ('field_y', '!=', False),
            ...     '|',
            ...     ('field_x', 'in', (1,)),
            ...     ('field_x', 'in', (2,))
            ... ])
            >>> domain3.simplified
            ['&', ('field_x', 'in', (1,)), ('field_y', '!=', False)]

        """
        return DomainTree(self.second_normal_form).get_simplified_domain()

    def distribute_not(self):
        """Return a new domain without `not` operators.

        For instance, having ``domain`` value like::

            >>> domain = Domain([
            ...     '!', ('field_x', '!=', False),
            ...     '!', ('field_y', '=', 'value'),
            ...     '!', ('field_z', 'in', (1, 2, 3)),
            ...     '!', ('field_w', '>', 1),
            ... ])

            >>> domain.distribute_not()
            [
                '&',
                '&',
                '&',
                ('field_x', '=', False),
                ('field_y', '!=', 'value'),
                ('field_z', 'not in', (1, 2, 3)),
                ('field_w', '<=', 1)
            ]

        """
        return Domain(this.distribute_not(self.first_normal_form))

    @crossmethod
    def AND(*domains):
        """Join given domains using `and` operator.

        :return: A domain if first normal form.

        """
        return Domain(this.AND([Domain(domain).second_normal_form for domain in domains]))

    __and__ = __rand__ = AND

    @crossmethod
    def OR(*domains):
        """Join given domains using `or` operator.

        :return: A domain if first normal form.

        """
        return Domain(this.OR([Domain(domain).second_normal_form for domain in domains]))

    __or__ = __ror__ = OR

    def __invert__(self):
        return Domain(["!"] + self.second_normal_form)

    def __eq__(self, other):
        """Two domains are equivalent if both have similar DomainTree."""
        # TODO: In logic, we can identify two predicates if: a implies
        # b and b implies a, although this has nothing to do with them being
        # the *same* predicate.  However, since this implementation only
        # yields True when both domains have the same hash, we can find a, b
        # such that a implies b and b implies a, but a != b.
        other = Domain(other)
        return hash(self) == hash(other)

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash(DomainTree(self.second_normal_form))

    def asfilter(self, this="this", *, convert_false=True, convert_none=False):
        """Return a callable which is equivalent to the domain.

        This method translates the domain to a `ast.Lambda <ast>`:mod: and
        compiles it.

        The main property is that is ``res`` is the result of a
        ``search(domain)``; then filtering by ``domain.asfilter()`` does not
        filter-out any record.

        The domain cannot use 'child_of', '=like' or '=ilike'.

        :param this: The name of the argument in the lambda.  All attributes
            in the domain are get from this argument.

        :keyword convert_false: If True (the default) terms of the form
               ``(x, '=', False)`` are translated to ``not x`` and terms of
               the form ``(x, '!=', False)`` are translated to ``bool(x)``.
               If `convert_false` is False they get translated to
               ``x = False``, ``x != False``.

        :keyword convert_none: Similar to `convert_false` but for None.

                 If `convert_none` is False (the default), terms like
                 ``(x, '=', None)`` are translated using ``is``:
                 ``x is None``.

        .. note:: In Python ``0 == False``, so Odoo treats 0 specially in the
                  context of 'not in' and 'in'.  See `PR 31408`__ for more
                  information.  However, `convert_false` only takes into
                  account actual False values and terms like ``(x, '=', 0)``
                  are not affected.

        __ https://github.com/odoo/odoo/pull/31408


        The lambda created for::

            Domain([('state', 'in', ('draft', 'open'))]).asfilter()

        is equivalent to::

            lambda this: this.state in ('draft', 'open')

        .. rubric:: Traversing fields in domains

        If your domain uses field traversal (e.g ``('line_ids.state', ...)``)
        the generated lambda will use ``mapped()`` and ``filtered()`` instead
        of simple ``ast.Attribute`` nodes.  Thus the lambda for::

          Domain([('order_id.line_ids.state', '=', 'open')]).asfilter(this='t')

        is equivalent to::

          lambda t: (t.mapped('order_id.line_ids')
                      .filtered(lambda r: r.state == 'open'))

        .. versionadded:: 0.54.0

        .. versionchanged:: 0.55.0 Change the behavior of fields traversal, so
           that filters over x2many fields work.

        .. versionchanged:: 0.82.0 Add parameters `convert_false` and `convert_none`.

        """
        return eval(
            compile(
                self._get_filter_ast(this, convert_false=convert_false, convert_none=convert_none),
                "<domain>",
                "eval",
            )
        )

    def _get_filter_ast(self, this="this", *, convert_false=True, convert_none=False):
        """Get compilable AST of the lambda obtained by `get_filter`:func:."""
        stack = []
        for kind, term in self.walk():
            if kind == KIND_TERM:
                fieldname, op, value = term
                constructor = _TERM_CONSTRUCTOR[op]
                stack.append(
                    constructor(
                        this,
                        fieldname,
                        value,
                        convert_false=convert_false,
                        convert_none=convert_none,
                    )
                )
            else:
                assert kind == KIND_OPERATOR
                if term in BINARY_OPERATORS:
                    args = (stack.pop(), stack.pop())
                else:
                    args = (stack.pop(),)
                constructor = _TERM_CONSTRUCTOR[term]
                stack.append(constructor(*args))
        node = stack.pop()
        assert not stack, "Remaining nodes in the stack: {}".format(stack)
        fn = ql.ensure_compilable(ql.Expression(ql.Lambda(ql.make_arguments(this), node)))
        return fn

    def walk(self):
        """Performs a post-fix walk of the domain's second normal form.

        Yields tuples of ``(kind, what)``.  `kind` can be either 'TERM' or
        'OPERATOR'.  `what` will be the term or operator.  For `term` it will
        the tuple ``(field, operator, arg)`` in Odoo domains.  For `operator`
        it will be the string identifying the operator.

        Example:

           >>> from xoeuf.osv.expression import Domain
           >>> d = Domain([('a', '=', 1), ('b', '=', 2), ('c', '=', 3)])
           >>> list(d.walk())
           [('TERM', ('a', '=', 1)),
            ('TERM', ('b', '=', 2)),
            ('TERM', ('c', '=', 3)),
            ('OPERATOR', '&'),
            ('OPERATOR', '&')]

        .. versionadded:: 1.1.0

        """
        # Since the only operators we have in 2NF are AND and OR the postfix is simply
        # the reversed prefix notation of domains.
        for term in reversed(self.second_normal_form):
            if this.is_leaf(term):
                yield "TERM", term
            else:
                yield "OPERATOR", term


class DomainTerm(object):
    def __init__(self, term):
        if isinstance(term, DomainTerm):
            term = term.original
        self.original = term
        term = normalize_leaf(term)
        self.normalized = term
        if this.is_operator(term):
            self.is_operator = True
            self.operator = term
            self.is_leaf = self.left = self.right = False
        elif this.is_leaf(term):
            self.is_operator = False
            self.is_leaf = True
            self.left, self.operator, self.right = term
        else:
            # TODO: May be a # TypeError.
            raise ValueError("Invalid domain term %r" % (term,))

    def __getitem__(self, x):
        if self.is_leaf:
            return (self.left, self.operator, self.right)[x]
        else:
            return self.operator[x]

    def __eq__(self, other):
        if not isinstance(other, DomainTerm):
            other = DomainTerm(other)
        return hash(self) == hash(other)

    def __ne__(self, other):
        return not self == other

    def __repr__(self):
        if self.original == self.normalized:
            return repr(self.original)
        else:
            return "%r => %r" % (self.original, self.normalized)

    operators_implication = {
        "=?": lambda x, y: operator.eq(x, y) or y is False,
        ">": operator.ge,
        ">=": operator.ge,
        "<": operator.le,
        "<=": operator.le,
        "in": lambda x, y: all(i in y for i in x),
        "not in": lambda x, y: all(i in x for i in y),
        "like": lambda x, y: x.find(y) >= 0,
        # TODO: asd_g imply asdfg `_` == any character
        "=like": lambda x, y: x.find(y) >= 0,
        "not like": lambda x, y: y.find(x) >= 0,
        "ilike": lambda x, y: x.lower().find(y.lower()) >= 0,
        # TODO: asd_g imply asdfg `_` == any character
        "=ilike": lambda x, y: x.lower().find(y.lower()) >= 0,
        "not ilike": lambda x, y: y.lower().find(x.lower()) >= 0,
    }

    def implies(self, other):
        other = DomainTerm(other)
        # equals terms are implied.
        if self == other:
            return True
        # terms which different left operand can't be compared.
        elif self.left != other.left:
            return False
        elif self.is_operator:
            # & => &
            return self.operator == other.operator
        else:
            # (x = 1)  => (x = 1)
            # (x > 1) => (x > 0)
            # (x in (1,2,3)) => (x in (1,2,3,4))
            if self.operator == other.operator:
                compare = self.operators_implication.get(other.operator)
                return compare(self.right, other.right) if compare else False
            else:
                # TODO: x = 1  implies x != 2; x = 2 1 implies x > 1
                return False

    def __hash__(self):
        return hash(self.normalized)


class DomainTree(object):
    """Tree structure to express Odoo domains.

    .. warning:: This class in not a public API of this model.  Its attributes
       may change in incompatible ways from one release to the other.

    A domain like this::

      [
          '&',
          '&',
          ('field_y', '!=', False),
          ('field_x', '=', 'value'),
          '|',
          ('field_z', 'in', (1, 2, 3)),
          ('field_w', '>', 1)
      ]

    Is represented like this::

                                     +-----+
                                     | '&' |
                                     +--+--+
                                        |
                   +--------------------+------------------------+
                   |                    |                        |
      +------------+-----------+ +------+------------------+  +--+--+
      |('field_y', '!=', False)| |('field_x', '=', 'value')|  | '|' |
      +------------------------+ +-------------------------+  +--+--+
                                                                 |
                                  +------------------------------+--------+
                                  |                                       |
                     +------------+---------------+       +---------------+---+
                     |('field_z', 'in', (1, 2, 3))|       |('field_w', '>', 1)|
                     +----------------------------+       +-------------------+

    .. warning:: The domain must be in the second normal form.

    """

    def __init__(self, domain, parent=None):
        term = domain.pop(0)
        self.term = DomainTerm(term)
        self.parent = parent
        if term in this.DOMAIN_OPERATORS:
            count = 2  # minimum number of operand in an operation.
            children = set()
            while count:
                if domain[0] == term:
                    count += 1
                    domain.pop(0)
                else:
                    child = DomainTree(domain, self)
                    # A & ((B & C) | A) should be simplified as A & B & C
                    if child.term == self.term:
                        children |= child.children
                    else:
                        children.add(child)
                    count -= 1
            # if a tree node have only one child it be come into it child.
            if len(children) == 1:
                child = children.pop()
                self.term = child.term
                self.children = child.children
            else:
                self.children = children
        else:
            self.children = set()
        self._simplify()

    @property
    def is_operator(self):
        return self.term in this.DOMAIN_OPERATORS

    @property
    def is_leaf(self):
        return not self.is_operator

    def _simplify(self):
        """Remove redundant branches."""
        for child in set(self.children):
            if self.term == this.AND_OPERATOR:
                # If current `child` is implied by any other ignore it.
                func = lambda x, y: y.implies(x)  # noqa
            else:
                # If current `child` implies any other ignore it.
                func = lambda x, y: x.implies(y)  # noqa
            if any(func(child, y) for y in self.children - {child}):
                self.children.remove(child)
        if len(self.children) == 1:
            _self = self.children.pop()
            self.children = _self.children
            self.term = _self.term

    @property
    def sorted_children(self):
        # TODO: Sort by hash is weird.  What does it mean?
        return sorted(self.children, key=lambda item: hash(item))

    def get_simplified_domain(self):
        if self.parent:
            res = Domain(self.term.original for x in range(1, len(self.children) or 2))
        elif self.is_leaf:
            res = Domain([self.term.original])
        else:
            # Initials `&` aren't needed.
            res = Domain([self.term.original] if self.term == this.OR_OPERATOR else [])
        if not self.is_leaf:
            res.extend(chain(*(x.get_simplified_domain() for x in self.sorted_children)))
        return res

    def __repr__(self):
        if self.is_leaf:
            return repr(self.term)
        else:
            return "(%s)" % (" %r " % (self.term,)).join(
                repr(child) for child in self.sorted_children
            )

    def __eq__(self, other):
        if self.is_leaf == other.is_leaf:
            if self.is_leaf:
                return self.term == other.term
            else:
                return self.term == other.term and not self.children ^ other.children  # noqa
        return False

    def __ne__(self, other):
        return not self == other

    def implies(self, other):
        funct = all if other.term == this.AND_OPERATOR else any
        if self.is_leaf:
            # A => A
            if self.term.implies(other.term):
                return True
            # A => A | B
            if other.is_operator and funct(self.implies(child) for child in other.sorted_children):
                return True
        elif self.is_operator:
            funct2 = any if self.term == this.AND_OPERATOR else all
            # A & B => A
            if funct2(child.implies(other) for child in self.sorted_children):
                return True
            # A & B => A | B
            if funct(
                funct2(child.implies(other_child) for child in self.sorted_children)
                for other_child in other.sorted_children
            ):
                return True
        return False

    def __hash__(self):
        return hash(tuple([self.term] + self.sorted_children))

    @deprecated("Domain.walk()")
    def walk(self):
        """Performs a post-fix walk of the tree.

        Yields tuples of ``(kind, what)``.  `kind` can be either 'TERM' or
        'OPERATOR'.  `what` will be the term or operator.  For `term` it will
        the tuple ``(field, operator, arg)`` in Odoo domains.  For `operator`
        it will be the string identifying the operator.

        Despite that the tree allows AND (``&``) and OR (``|``) operator to
        have more than two children, we generate OPERATOR items for the
        equivalent binary expression tree::

           >>> from xoeuf.osv.expression import Domain, DomainTree
           >>> d = Domain([('a', '=', 1), ('b', '=', 2), ('c', '=', 3)])
           >>> tree = DomainTree(d.second_normal_form)
           >>> list(tree.walk())
           [('TERM', ('a', '=', 1)),
            ('TERM', ('c', '=', 3)),
            ('TERM', ('b', '=', 2)),
            ('OPERATOR', '&'),
            ('OPERATOR', '&')]

        .. deprecated:: 1.1.0

           DomainTree always simplify its input.  The walk is not a syntactical walk of
           the input but of its simplified form.  Since all operators are commutative,
           the order of the children may differ widely from run to the other.  But
           short-circuit of AND/OR operators may be affected.

        """
        if self.is_leaf:
            yield (KIND_TERM, self.term.original)
        else:
            for which in self.children:
                for what in which.walk():
                    yield what
            yield (KIND_OPERATOR, self.term)
            # Since the tree groups more than two children under a single
            # instance of binary operator, we have to yield it once per pair.
            if self.term.original in BINARY_OPERATORS:
                for _ in range(len(self.children) - 2):
                    yield (KIND_OPERATOR, self.term)


# Exports AND and OR so that we can replace 'from odoo.
def AND(domains):
    return Domain.AND(*domains)


def OR(domains):
    return Domain.OR(*domains)


def _constructor_not(node):
    return ql.UnaryOp(ql.Not(), node)


def _constructor_and(*operands):
    return ql.BoolOp(ql.And(), list(operands))


def _constructor_or(*operands):
    return ql.BoolOp(ql.Or(), list(operands))


def _get_mapped(node, fieldname):
    attrs, field = fieldname.rsplit(".", 1)
    mapped_fn = ql.make_attr(node, "mapped")
    return (ql.make_call(mapped_fn, _constructor_from_value(attrs)), field)


def _constructor_getattr(node, fieldname):
    if isinstance(fieldname, str):
        if "." in fieldname:
            result = _get_mapped(node, fieldname)
        else:
            result = ql.make_attr(node, fieldname)
    else:
        result = _constructor_from_value(fieldname)
    return result


def _get_constructor(qst):
    """Return a constructor for AST for a term `(fielname, <op>, value)`.

    :param qst: Any of the operators AST classes available for comparisons.

    The result is a function that with signaure ``(this, fieldname, value)``.

    :param this: The AST node to which the operation is applied.

    :param fieldname: The name of the field being operated upon.

    :param value: The second operand of the operator.

    If the fieldname doesn't contain a dot '.'; return a simple AST.  A domain
    like::

        Domain(['state', '=', 'open']).asfilter()

    yields a callable equivalent to::

        lambda this: this.state == 'open'

    If the fieldname contains a dot '.'; return an AST using ``mapped()`` and
    ``filtered()`` as appropriate:

        Domain(['parent_id.children_ids.state', '=', 'open']).asfilter()

    yields a callable equivalent to::

        lambda this: this.mapped('parent_id.children_ids').filtered(
            lambda r: r.state == 'open'
        )

    """

    # We ignore convert_false and convert_none here
    def result(this, fieldname, value, *, convert_false=None, convert_none=None):
        node = _constructor_getattr(ql.Name(this, ql.Load()), fieldname)
        if not isinstance(node, tuple):
            return ql.Compare(node, [qst()], [_constructor_from_value(value)])
        else:
            # node.filtered(lambda x: x.field <CMP> <value>)
            mapped, field = node
            lambda_ast = ql.Lambda(
                ql.make_arguments("x"),
                ql.Compare(
                    ql.make_attr(ql.Name("x", ql.Load()), field),
                    [qst()],
                    [_constructor_from_value(value)],
                ),
            )
            filtered_fn = ql.make_attr(mapped, "filtered")
            return ql.make_call(filtered_fn, lambda_ast)

    return result


def _get_constructor_alt(weak_qst, strong_qst, negate=_constructor_not):
    """The same as _get_constructor but returns a filter that takes None into
    account and uses a stronger QST comparator (usually Is and IsNot ) when
    the value is None.

    """

    def result(this, fieldname, value, *, convert_false, convert_none):
        node = _constructor_getattr(ql.Name(this, ql.Load()), fieldname)
        if not isinstance(node, tuple):
            if value is False and convert_false:
                return negate(node)
            elif value is None:
                if convert_none:
                    return negate(node)
                else:
                    return ql.Compare(node, [strong_qst()], [_constructor_from_value(value)])
            else:
                return ql.Compare(node, [weak_qst()], [_constructor_from_value(value)])
        else:
            mapped, field = node
            which = ql.make_attr(ql.Name("x", ql.Load()), field)
            if value is False and convert_false:
                body = negate(which)
            elif value is None:
                if convert_none:
                    body = negate(which)
                else:
                    body = ql.Compare(which, [strong_qst()], [_constructor_from_value(value)])
            else:
                body = ql.Compare(which, [weak_qst()], [_constructor_from_value(value)])
            lambda_ast = ql.Lambda(ql.make_arguments("x"), body)
            filtered_fn = ql.make_attr(mapped, "filtered")
            return ql.make_call(filtered_fn, lambda_ast)

    return result


_constructor_eq = _get_constructor_alt(ql.Eq, ql.Is)
_constructor_ne = _get_constructor_alt(ql.NotEq, ql.IsNot, negate=lambda x: x)

_constructor_le = _get_constructor(ql.LtE)
_constructor_lt = _get_constructor(ql.Lt)
_constructor_ge = _get_constructor(ql.GtE)
_constructor_gt = _get_constructor(ql.Gt)


def _constructor_in(this, fieldname, value, qst=ql.In, *, convert_false=None, convert_none=None):
    """Create the AST for a term `(fielname, '[not ]in', value)`.

    The difference with `standard <_get_constructor>`:func: constructors is
    that, to comply with Odoo's interpretation of 'in' and 'not in', this
    function removes any 0 or False in `value`.

    """
    # Filtering False is the same Odoo does; which causes 0 to be removed
    # also.  See https://github.com/odoo/odoo/pull/31408
    assert qst in (ql.In, ql.NotIn)
    value = [x for x in value if x != False]  # noqa
    return _get_constructor(qst)(
        this, fieldname, value, convert_false=convert_false, convert_none=convert_none
    )


def _constructor_not_in(this, fieldname, value, *, convert_false=None, convert_none=None):
    return _constructor_in(
        this,
        fieldname,
        value,
        qst=ql.NotIn,
        convert_false=convert_false,
        convert_none=convert_none,
    )


def _constructor_like(this, fieldname, value, qst=ql.In, *, convert_false=None, convert_none=None):
    """Create the AST for a term `(fielname, '[not ]like', value)`.

    We use 'in' ('not in') Python operators; so the procedure AST are those
    matching syntax 'value in this.fieldname' when fieldname doesn't contain a
    dot.  If `fieldname` contains a dot the result changes to::

       headattrs, lastattr = fiedname.rsplit('.', 1)
       this.mapped(headattrs).filtered(lambda r: value in getattr(r, lastattr))

    """
    assert qst in (ql.In, ql.NotIn)
    node = _constructor_getattr(ql.Name(this, ql.Load()), fieldname)
    if isinstance(node, tuple):
        # this.mapped(attrs).filtered(lambda r: value in r.field)
        mapped, field = node
        lambda_arg = ql.Lambda(
            ql.make_arguments("r"),
            ql.Compare(
                _constructor_from_value(value),
                [qst()],
                [ql.make_attr(ql.Name("r", ql.Load()), field)],
            ),
        )
        fn = ql.make_attr(mapped, "filtered")
        return ql.make_call(fn, lambda_arg)
    else:
        # ``value in this.fieldname``
        return ql.Compare(_constructor_from_value(value), [qst()], [node])


def _constructor_not_like(this, fieldname, value, *, convert_false=None, convert_none=None):
    return _constructor_like(
        this,
        fieldname,
        value,
        qst=ql.NotIn,
        convert_false=convert_false,
        convert_none=convert_none,
    )


def _constructor_ilike(this, fieldname, value, qst=ql.In, *, convert_false=None, convert_none=None):
    assert qst in (ql.In, ql.NotIn)
    node = _constructor_getattr(ql.Name(this, ql.Load()), fieldname)
    if isinstance(node, tuple):
        # this.mapped(attrs).filtered(lambda r: value.lower() in r.field.lower())``
        mapped, field = node
        lambda_arg = ql.Lambda(
            ql.make_arguments("r"),
            ql.Compare(
                ql.make_argless_call(_constructor_getattr(_constructor_from_value(value), "lower")),
                [qst()],
                [
                    ql.make_argless_call(
                        ql.make_attr(ql.make_attr(ql.Name("r", ql.Load()), field), "lower")
                    )
                ],
            ),
        )
        fn = ql.make_attr(mapped, "filtered")
        return ql.make_call(fn, lambda_arg)
    else:
        # ``value.lower() in this.fieldname.lower()``
        node = _constructor_getattr(node, "lower")
        fn = ql.make_argless_call(node)
        return ql.Compare(
            ql.make_argless_call(_constructor_getattr(_constructor_from_value(value), "lower")),
            [qst()],
            [fn],
        )


def _constructor_not_ilike(this, fieldname, value, *, convert_false=None, convert_none=None):
    return _constructor_ilike(
        this,
        fieldname,
        value,
        qst=ql.NotIn,
        convert_false=convert_false,
        convert_none=convert_none,
    )


def _constructor_from_value(value):
    expr = ql.parse(repr(value))
    return expr.body


_TERM_CONSTRUCTOR = {
    "!": _constructor_not,
    "&": _constructor_and,
    "|": _constructor_or,
    "=": _constructor_eq,
    "==": _constructor_eq,
    "=?": _constructor_eq,
    "!=": _constructor_ne,
    "<>": _constructor_ne,
    "<=": _constructor_le,
    "<": _constructor_lt,
    ">=": _constructor_ge,
    ">": _constructor_gt,
    "in": _constructor_in,
    "not in": _constructor_not_in,
    "like": _constructor_like,
    "ilike": _constructor_ilike,
    "not like": _constructor_not_like,
    "not ilike": _constructor_not_ilike,
}
