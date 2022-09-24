#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Copyright (c) Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can do what the LICENCE file allows you to.
#
import logging
from datetime import datetime
from itertools import product

from hypothesis import strategies as s, given, settings
from hypothesis.stateful import RuleBasedStateMachine, rule, Bundle
from hypothesis.stateful import run_state_machine_as_test

from xoeuf.osv import expression as expr
from xoeuf.osv import ql
from xoeuf.osv.expression import Domain

from xotl.tools.future.collections import opendict

from odoo.osv import expression as odoo_expr
from odoo.tests.common import TransactionCase, BaseCase

names = s.text(alphabet="abdefgh", min_size=1, max_size=5)
operators = s.sampled_from(["=", "!=", "<", ">", "<>"])
all_operators = s.sampled_from(
    ["=", "!=", "<", ">", "<>", "like", "ilike", "not like", "not ilike"]
)
ages = s.integers(min_value=0, max_value=120)
sensible_values = s.integers(min_value=-10, max_value=10)

# Logical connectors with the amount of terms it connects.  Notice that ''
# takes two arguments because it's the same as '&'.
connectors = s.sampled_from([("", 2), ("&", 2), ("!", 1), ("|", 2)])

logger = logging.getLogger(__name__)


@s.composite
def terms(draw, fields=None, values=None):
    if not values:
        values = sensible_values
    f = fields or names
    name = str(draw(f))
    operator = draw(operators)
    value = draw(values)
    return (name, operator, value)


@s.composite
def domains(draw, fields=None, min_size=1, max_size=10):
    leaves = draw(s.lists(terms(fields), min_size=min_size, max_size=max_size))
    result = []
    while leaves:
        connector, many = draw(connectors)
        if many <= len(leaves):
            if connector:
                result.append(connector)
            result.extend(leaves[:many])
            leaves = leaves[many:]
        elif len(leaves) == 1:
            result.append(leaves.pop(0))
    return Domain(result)


class TestDomain(BaseCase):
    @given(domains())
    def test_first_normal_form_idempotency(self, domain):
        self.assertEqual(
            domain.first_normal_form, domain.first_normal_form.first_normal_form
        )

    @given(domains())
    def test_second_normal_form_idempotency(self, domain):
        self.assertEqual(
            domain.second_normal_form, domain.second_normal_form.second_normal_form
        )

    @given(domains())
    def test_versions_equivalency(self, domain):
        # Any domain must be equivalent in all its versions.
        all_versions = [
            domain,
            domain.simplified,
            domain.first_normal_form,
            domain.second_normal_form,
        ]
        for version1, version2 in product(all_versions, all_versions):
            self.assertEqual(version1, version2, msg="%r != %r" % (version1, version2))

    @settings(deadline=1000)
    @given(domains())
    def test_simplified(self, domain):
        # A simplified domain never start with '&' operator.
        self.assertNotEqual(
            domain.simplified[0],
            expr.AND_OPERATOR,
            msg="%r start with &" % domain.simplified,
        )
        # The simplified domain must be the shortest.
        all_versions = [domain, domain.first_normal_form, domain.second_normal_form]
        for version in all_versions:
            self.assertLessEqual(
                len(domain.simplified),
                len(version),
                msg="len(%r) > len(%r)" % (domain.simplified, version),
            )
        self.assertTrue(
            all(
                odoo_expr.is_leaf(term) or odoo_expr.is_operator(term)
                for term in domain.simplified
            )
        )

    @given(domains())
    def test_simplified_idempotency(self, domain):
        self.assertEqual(domain.simplified, domain.simplified.simplified)

    @given(s.lists(domains(), min_size=2, max_size=10))
    def test_expr_replacement(self, domains):
        expr.AND(domains)
        odoo_expr.AND(domains)

    def test_eq(self):
        A = Domain([("field_x", "=", 1)])
        # A == A
        self.assertTrue(A == A)

        # ~A == ~A
        self.assertTrue(~A == ~A)

        # (x = 1)  == ! (x <> 1)
        A1 = Domain(["!", ("field_x", "<>", 1)])
        self.assertTrue(A == A1)

    def test_implies(self):
        # Basic implications.
        # -------------------

        A = Domain([("field_x", "=", 1)])
        B = Domain([("field_y", "!=", False)])

        # A => A
        self.assertTrue(A.implies(A))

        # A => A | B
        self.assertTrue(A.implies(A | B))

        # A & B => A
        self.assertTrue((A & B).implies(A))

        # A & B => A | B
        self.assertTrue((A & B).implies(A | B))

        self.assertEqual(Domain.AND(list(A), B), (A & B))
        self.assertEqual(expr.AND([list(A), B]), (A & B))

        # Inter terms implications.
        # -------------------------

        # (x = 1)  => (x = 1)
        A = Domain([("field_x", "=", 1)])
        A1 = Domain([("field_x", "=", 1)])
        self.assertTrue(A.implies(A1))

        # (x != 1)  => (x <> 1)
        A = Domain([("field_x", "!=", 1)])
        A1 = Domain([("field_x", "<>", 1)])
        self.assertTrue(A.implies(A1))

        # (x > 1) => (x > 0)
        A = Domain([("field_x", ">", 10)])
        A1 = Domain([("field_x", ">", 1)])
        self.assertTrue(A.implies(A1))

        # (x in (1,2,3)) => (x in (1,2,3,4))
        A = Domain([("field_x", "in", (1, 2, 3))])
        A1 = Domain([("field_x", "in", (1, 2, 3, 4))])
        self.assertTrue(A.implies(A1))
        #

        # Compound implications.
        # ----------------------
        # A => B & C iff (A => B) & (A => C)
        A = Domain([("field_x", "in", (1, 4))])
        B = Domain([("field_x", "in", (1, 2, 4))])
        C = Domain([("field_x", "in", (1, 3, 4))])
        self.assertTrue(A.implies(B))
        self.assertTrue(A.implies(C))
        self.assertTrue(A.implies(B & C))

        # More complex implications
        # -------------------------

        x = Domain(
            [
                "|",
                ("field_y", "!=", False),
                ("field_x", "=", "value"),
                ("field_z", "in", (1,)),
            ]
        )
        y = Domain(
            [
                "|",
                ("field_y", "!=", False),
                ("field_x", "=", "value"),
                ("field_z", "in", (1, 2, 3)),
                "|",
                ("field_x", "=", "value"),
                ("field_y", "!=", False),
            ]
        )
        assert x.implies(y)

        x = Domain(
            [
                ("field_y", "!=", False),
                ("field_z", "in", (1,)),
                ("field_z", "in", (1, 2)),
                "|",
                ("field_y", "!=", False),
                "|",
                ("field_z", "in", (1,)),
                ("field_z", "in", (2,)),
            ]
        )
        y = Domain([("field_y", "!=", False), ("field_z", "in", (1, 2, 3))])
        assert x.implies(y)

    def test_walk(self):
        y = Domain(
            [
                "|",
                ("a", "!=", False),
                ("b", "=", "value"),
                ("c", "in", (1, 2, 3)),
                "|",
                "|",
                "!",
                ("d", "=", "value"),
                ("f", "!=", False),
                ("g", "=", "h"),
            ]
        )
        expected = [
            ("TERM", ("g", "=", "h")),
            ("TERM", ("f", "!=", False)),
            ("TERM", ("d", "!=", "value")),
            ("OPERATOR", "|"),
            ("OPERATOR", "|"),
            ("TERM", ("c", "in", (1, 2, 3))),
            ("TERM", ("b", "=", "value")),
            ("TERM", ("a", "!=", False)),
            ("OPERATOR", "|"),
            ("OPERATOR", "&"),
            ("OPERATOR", "&"),
        ]
        self.assertEqual(expected, list(y.walk()))


class TestDomainFilter(BaseCase):
    def test_get_filter_ast_simple_one_term_with_in(self):
        self.assertEqual(
            Domain([("state", "in", [1, 2])])._get_filter_ast(),
            ql.Expression(
                ql.Lambda(
                    ql.make_arguments("this"),
                    expr._constructor_in("this", "state", [1, 2]),
                )
            ),
        )

    def test_empty_domain(self):
        self.assertTrue(Domain([]).asfilter()(0))

    def test_regression_asfilter_with_datetime(self):
        objects = [opendict(date_from=datetime(2020, 6, 5))]
        domain = Domain([("date_from", ">=", datetime(2020, 1, 1))])
        list(filter(domain.asfilter(), objects))

    def assertASTEqual(self, e1, e2):
        self.assertEqual(
            e1,
            e2,
            msg=f"Different ASTs:\n{e1!s}\n **** is not equal to ****\n {e2!s}\n",
        )

    def test_asfilter_equal_false(self):
        for query_operator, python_expr in (("=", "not"), ("!=", "")):
            query = Domain([("attr", query_operator, False)])
            ast = query._get_filter_ast()
            expected = ql.parse(f"lambda this: {python_expr} this.attr")
            self.assertASTEqual(ast, expected)

    def test_asfilter_equal_false_with_mapped_filtered(self):
        for query_operator, python_expr in (("=", "not"), ("!=", "")):
            query = Domain([("parent.attr", query_operator, False)])
            ast = query._get_filter_ast()
            expected = ql.parse(
                f"lambda this: this.mapped('parent').filtered(lambda x: {python_expr} x.attr)"
            )
            self.assertASTEqual(ast, expected)

    def test_asfilter_equal_false_with_convert_false_unset(self):
        for query_operator, python_operator in (("=", "=="), ("!=", "!=")):
            query = Domain([("attr", query_operator, False)])
            ast = query._get_filter_ast(convert_false=False)
            expected = ql.parse(f"lambda this: this.attr {python_operator} False")
            self.assertASTEqual(ast, expected)

    def test_asfilter_equal_false_with_convert_false_unset_mapped_filtered(self):
        for query_operator, python_operator in (("=", "=="), ("!=", "!=")):
            query = Domain([("parent.attr", query_operator, False)])
            ast = query._get_filter_ast(convert_false=False)
            expected = ql.parse(
                f"lambda this: this.mapped('parent').filtered(lambda x: x.attr {python_operator} False)"  # noqa
            )
            self.assertASTEqual(ast, expected)

    def test_asfilter_equal_none(self):
        for query_operator, python_expr in (("=", "not"), ("!=", "")):
            query = Domain([("attr", query_operator, None)])
            ast = query._get_filter_ast(convert_none=True)
            expected = ql.parse(f"lambda this: {python_expr} this.attr")
            self.assertASTEqual(ast, expected)

    def test_asfilter_equal_none_with_convert_none_unset(self):
        for query_operator, python_operator in (("=", "is"), ("!=", "is not")):
            query = Domain([("attr", query_operator, None)])
            ast = query._get_filter_ast()
            expected = ql.parse(f"lambda this: this.attr {python_operator} None")
            self.assertASTEqual(ast, expected)

    def test_asfilter_equal_none_with_mapped_filtered(self):
        for query_operator, python_operator in (("=", "is"), ("!=", "is not")):
            query = Domain([("parent.attr", query_operator, None)])
            ast = query._get_filter_ast()
            expected = ql.parse(
                f"lambda this: this.mapped('parent').filtered(lambda x: x.attr {python_operator} None)"  # noqa
            )
            self.assertASTEqual(ast, expected)


def get_model_domain_machine(this):
    Model = this.env["test_domain.model"]

    class ModelDomainMachine(RuleBasedStateMachine):
        objects = Bundle("objects")

        @rule(target=objects, name=names, age=ages)
        def create_object(self, name, age):
            logger.info("Creating object name: %s, age: %s", name, age)
            return Model.create({"name": name, "age": age})

        @rule(target=objects, name=names, age=ages, parent=objects)
        def create_child_object(self, name, age, parent):
            return Model.create({"name": name, "age": age, "parent_id": parent.id})

        @rule(age=ages, op=operators)
        def find_by_age(self, age, op):
            query = Domain([("age", op, age)])
            res = Model.search(query)
            logger.info("Check filter/domain: %s; count: %s", query, len(res))
            this.assertEqualRecordset(res.filtered(query.asfilter()), res)

        @rule(
            age=ages,
            op=operators,
            path=s.lists(
                s.sampled_from(["parent_id", "children_ids"]), min_size=1, max_size=4
            ),
        )
        def find_by_parent_age(self, age, op, path):
            attr = ".".join(path) + ".age"
            query = Domain([(attr, op, age)])
            res = Model.search(query)
            logger.info("Check filter/domain: %s; count: %s", query, len(res))
            this.assertEqualRecordset(res.filtered(query.asfilter()), res)

        @rule(ages=s.lists(ages))
        def find_by_ages(self, ages):
            query = Domain([("age", "in", ages)])
            res = Model.search(query)
            logger.info("Check filter/domain: %s; count: %s", query, len(res))
            this.assertEqualRecordset(res.filtered(query.asfilter()), res)

        @rule(
            ages=s.lists(ages),
            path=s.lists(
                s.sampled_from(["parent_id", "children_ids"]), min_size=1, max_size=4
            ),
        )
        def find_by_parent_ages(self, ages, path):
            attr = ".".join(path) + ".age"
            query = Domain([(attr, "in", ages)])
            res = Model.search(query)
            logger.info("Check filter/domain: %s; count: %s", query, len(res))
            this.assertEqualRecordset(res.filtered(query.asfilter()), res)

        @rule(ages=s.lists(ages))
        def find_by_not_ages(self, ages):
            query = Domain([("age", "not in", ages)])
            res = Model.search(query)
            logger.info("Check filter/domain: %s; count: %s", query, len(res))
            this.assertEqualRecordset(res.filtered(query.asfilter()), res)

        @rule(
            ages=s.lists(ages),
            path=s.lists(
                s.sampled_from(["parent_id", "children_ids"]), min_size=1, max_size=4
            ),
        )
        def find_by_path_not_ages(self, ages, path):
            attr = ".".join(path) + ".age"
            query = Domain([(attr, "not in", ages)])
            res = Model.search(query)
            logger.info("Check filter/domain: %s; count: %s", query, len(res))
            this.assertEqualRecordset(res.filtered(query.asfilter()), res)

        @rule(domain=domains(fields=s.just("age")))
        def find_by_arbitrary_domain(self, domain):
            res = Model.search(domain)
            logger.info("Check filter/domain: %s; count: %s", domain, len(res))
            this.assertEqualRecordset(res.filtered(domain.asfilter()), res)

        @rule(name=names, op=all_operators)
        def find_by_name(self, name, op):
            query = Domain([("name", op, name)])
            res = Model.search(query)
            logger.info("Check filter/domain: %s; count: %s", query, len(res))
            this.assertEqualRecordset(res.filtered(query.asfilter()), res)

        @rule(
            name=names,
            op=all_operators,
            path=s.lists(
                s.sampled_from(["parent_id", "children_ids"]), min_size=1, max_size=4
            ),
        )
        def find_by_path_name(self, name, op, path):
            attr = ".".join(path) + ".name"
            query = Domain([(attr, op, name)])
            res = Model.search(query)
            logger.info("Check filter/domain: %s; count: %s", query, len(res))
            this.assertEqualRecordset(res.filtered(query.asfilter()), res)

        @rule(names=s.lists(names))
        def find_by_names(self, names):
            query = Domain([("name", "in", names)])
            res = Model.search(query)
            logger.info("Check filter/domain: %s; count: %s", query, len(res))
            this.assertEqualRecordset(res.filtered(query.asfilter()), res)

        @rule(
            names=s.lists(names),
            path=s.lists(
                s.sampled_from(["parent_id", "children_ids"]), min_size=1, max_size=4
            ),
        )
        def find_by_path_names(self, names, path):
            attr = ".".join(path) + ".name"
            query = Domain([(attr, "in", names)])
            res = Model.search(query)
            logger.info("Check filter/domain: %s; count: %s", query, len(res))
            this.assertEqualRecordset(res.filtered(query.asfilter()), res)

        @rule(names=s.lists(names))
        def find_by_not_names(self, names):
            query = Domain([("name", "not in", names)])
            res = Model.search(query)
            logger.info("Check filter/domain: %s; count: %s", query, len(res))
            this.assertEqualRecordset(res.filtered(query.asfilter()), res)

        @rule(
            names=s.lists(names),
            path=s.lists(
                s.sampled_from(["parent_id", "children_ids"]), min_size=1, max_size=4
            ),
        )
        def find_by_path_not_names(self, names, path):
            attr = ".".join(path) + ".name"
            query = Domain([(attr, "not in", names)])
            res = Model.search(query)
            logger.info("Check filter/domain: %s; count: %s", query, len(res))
            this.assertEqualRecordset(res.filtered(query.asfilter()), res)

    return ModelDomainMachine


class TestConsistencyOfFilters(TransactionCase):
    def assertEqualRecordset(self, rs1, rs2):
        ours = rs1 - rs2
        theirs = rs2 - rs1
        self.assertEqual(
            rs1, rs2, msg="ours: {0!r}; theirs: {1!r}".format(ours, theirs)
        )

    def test_consistency_of_domains(self):
        run_state_machine_as_test(get_model_domain_machine(self))
