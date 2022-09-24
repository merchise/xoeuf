#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Copyright (c) Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can do what the LICENCE file allows you to.
#
from xoeuf import fields
from odoo.tests.common import TransactionCase

from .. import MIXIN_NAME


class TestReferences(TransactionCase):
    def test_simple_typed_reference(self):
        obj = self.env["test.model"].create({})
        typed_ref = obj._fields["typed_ref"]
        self.assertTrue(isinstance(typed_ref, fields.TypedReference))
        self.assertEqual(typed_ref.mixin, MIXIN_NAME)

        def typed_ref_assign(value):
            obj.typed_ref = value
            return True

        self.assertTrue(typed_ref_assign(False))
        obj2 = self.env["test.model1"].create({})
        self.assertTrue(typed_ref_assign(obj2))
        self.assertTrue(typed_ref_assign("%s,%d" % (obj2._name, obj2.id)))
        self.assertRaises(ValueError, typed_ref_assign, obj)

    def test_filtered_typed_reference(self):
        obj = self.env["test.model"].create({})

        def typed_ref_assign(value):
            obj.filtered_typed_ref = value
            return True

        obj2 = self.env["test.model1"].create({})
        # This should work, but the odoo validation is missing,
        # I am making a PR to propose it.
        # self.assertRaises(ValueError, typed_ref_assign, '%s,%d' % (obj2._name, obj2.id))
        self.assertRaises(ValueError, typed_ref_assign, obj2)

    def test_delegate_typed_reference(self):
        obj = self.env["test.model"].create({})
        obj2 = self.env["test.model1"].create({"test": "ok"})
        dummy_value = "any value"
        obj.test = dummy_value
        self.assertEqual(obj.test, dummy_value)
        obj.invalidate_cache()
        self.assertFalse(obj.test)
        obj.typed_ref = obj2
        obj.invalidate_cache()
        obj2.invalidate_cache()
        self.assertTrue(obj._fields["typed_ref"].delegate)
        self.assertTrue(obj._fields["test"].compute)
        self.assertEqual(obj.test, obj2.test)
        obj.test = "other value"
        self.assertEqual(obj.test, obj2.test)
        obj.invalidate_cache()
        obj2.invalidate_cache()
        self.assertEqual(obj.test, obj2.test)
        obj2.test = "other more value"
        # todo: indirect depends are not working fine.
        # self.assertEqual(obj.test, obj2.test)
        obj.invalidate_cache()
        obj2.invalidate_cache()
        self.assertEqual(obj.test, obj2.test)

    def test_related_field_setup(self):
        obj = self.env["test.model"]
        obj2 = self.env["test.model1"]
        # check related field attributes like: string, help, comodel_name, ...
        for attr, _ in obj._fields["partner_id"].related_attrs:
            self.assertEqual(
                getattr(obj._fields["partner_id"], attr),
                getattr(obj2._fields["partner_id"], attr),
            )

    def test_related_field_search(self):
        # computed non store field from a regular field
        self.env["test.model"].search([("test", "=", "any value")])
        # computed non store field from a computed non store field
        # self.env["test.model"].search([('comment', '=', 'any value')])  # no searchable
        # computed non store field from a computed store field
        self.env["test.model"].search([("street", "=", "any value")])
        # computed store field from a regular field
        self.env["test.model"].search([("test2", "=", "any value")])
        # computed store field from a computed store field
        self.env["test.model"].search([("ref", "=", "any value")])
        # computed store field from a computed non store field
        # self.env["test.model"].search([("name", "=", "any value")])

    def test_related_field_right_triggers(self):
        """All `store=False` computed field through a `Reference` are computed correctly.

        This behave is the same with any `Reference` odoo field.

        """
        obj = self.env["test.model1"].create(
            {"partner_id": self.env.user.partner_id.id}
        )
        obj2 = self.env["test.model"].create({"typed_ref": obj.reference_repr})
        dummy_value = "any value"

        # computed non store field from a regular field
        obj.test = dummy_value
        self.assertEqual(obj2.test, dummy_value)
        obj.invalidate_cache()
        obj2.invalidate_cache()
        self.assertEqual(obj2.test, dummy_value)

        # computed non store field from a computed non store field
        obj.comment = dummy_value
        self.assertEqual(obj2.comment, dummy_value)
        obj.invalidate_cache()
        obj2.invalidate_cache()
        self.assertEqual(obj2.comment, dummy_value)
        obj.partner_id.comment = dummy_value
        self.assertEqual(obj2.comment, dummy_value)
        obj.invalidate_cache()
        obj2.invalidate_cache()
        self.assertEqual(obj2.comment, dummy_value)

        # computed non store field from a computed store field
        obj.street = dummy_value
        self.assertEqual(obj2.street, dummy_value)
        obj.invalidate_cache()
        obj2.invalidate_cache()
        self.assertEqual(obj2.street, dummy_value)
        obj.partner_id.street = dummy_value
        self.assertEqual(obj2.street, dummy_value)
        obj.invalidate_cache()
        obj2.invalidate_cache()
        self.assertEqual(obj2.street, dummy_value)

    def test_related_field_wrong_triggers(self):
        """No `store=True` computed field through a `Reference` is computed correctly.

        The computed `store=True` fields from a `store=False` field through a
        `Reference` cause an` AttributeError` when writing on the source field.

        This behave is the same with any `Reference` odoo field.

        """
        obj = self.env["test.model1"].create(
            {"partner_id": self.env.user.partner_id.id}
        )
        obj2 = self.env["test.model"].create({"typed_ref": obj.reference_repr})
        dummy_value = "any value"

        # computed store field from a regular field
        obj.test2 = dummy_value
        self.assertNotEqual(obj2.test2, dummy_value)  # Is not updated
        obj.invalidate_cache()
        obj2.invalidate_cache()
        self.assertNotEqual(obj2.test2, dummy_value)  # Is not updated

        # computed store field from a computed store field
        obj.ref = dummy_value
        self.assertNotEqual(obj2.ref, dummy_value)  # Is not updated
        obj.invalidate_cache()
        obj2.invalidate_cache()
        self.assertNotEqual(obj2.ref, dummy_value)  # Is not updated

        # computed store field from a computed non store field
        # with self.assertRaises(AttributeError):
        #     obj.name = dummy_value
        # with self.assertRaises(AttributeError):
        #     obj.partner_id.name = dummy_value

    def test_related_field_inverse(self):
        obj = self.env["test.model1"].create(
            {"partner_id": self.env.user.partner_id.id}
        )
        obj2 = self.env["test.model"].create({"typed_ref": obj.reference_repr})
        dummy_value = "any value"

        # computed non store field from a regular field
        obj2.test = dummy_value
        self.assertEqual(obj.test, dummy_value)
        obj.invalidate_cache()
        obj2.invalidate_cache()
        self.assertEqual(obj.test, dummy_value)

        # computed non store field from a computed non store field
        obj2.comment = dummy_value
        self.assertEqual(obj.comment, dummy_value)
        self.assertEqual(obj.partner_id.comment, dummy_value)
        obj.invalidate_cache()
        obj2.invalidate_cache()
        self.assertEqual(obj.comment, dummy_value)
        self.assertEqual(obj.partner_id.comment, dummy_value)

        # computed non store field from a computed store field
        obj2.street = dummy_value
        self.assertEqual(obj.street, dummy_value)
        self.assertEqual(obj.partner_id.street, dummy_value)
        obj.invalidate_cache()
        obj2.invalidate_cache()
        self.assertEqual(obj.street, dummy_value)
        self.assertEqual(obj.partner_id.street, dummy_value)
