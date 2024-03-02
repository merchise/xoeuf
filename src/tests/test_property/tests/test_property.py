#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Copyright (c) Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can do what the LICENCE file allows you to.
#
from odoo.tests.common import TransactionCase

from xoeuf import fields


class TestProperty(TransactionCase):
    def setUp(self):
        super(TestProperty, self).setUp()
        Value = self.Value = self.env["test.property.value"]
        self.obj = Value.create({"value": "0123456789"})
        for val in "abcdefg":
            Value.create({"value": val})

    def test_setup(self):
        self.assertTrue(getattr(type(self.Value), "inverted_setup", False))

    def test_getter(self):
        obj = self.obj
        self.assertEqual(obj.inverted, "9876543210")

    def test_setter(self):
        obj = self.obj
        obj.inverted = "abcd"
        self.assertEqual(obj.value, "dcba")

    def test_deleter(self):
        obj = self.obj
        del obj.inverted
        self.assertIn(obj.value, (None, False))  # Odoo may xform None to False

    def test_nocreate(self):
        with self.assertRaises(AssertionError):
            # I would like that calling create would raise an exception, but
            # for now it just does not do anything.
            obj = self.Value.create({"inverted": "abcd"})
            self.assertEqual(obj.value, "dcba")

    def test_nowrite(self):
        with self.assertRaises(AssertionError):
            # I would like that calling search would raise an exception, but
            # for now it just does not do anything.
            self.obj.write({"inverted": "abcd"})
            self.assertEqual(self.obj.value, "dcba")

    # Don't perform the test of `search()` because it does not raise an
    # exception, but log an error that may fool our test scripts.

    def test_non_memoized_object(self):
        self.assertIsNot(self.obj.new_object, self.obj.new_object)

    def test_memoized_object(self):
        previous = self.obj.memoized_object
        self.assertIs(self.obj.memoized_object, previous)
        self.obj.memoized_object = sentinel = object()
        self.assertIs(self.obj.memoized_object, sentinel)
        self.assertIs(self.obj.memoized_object, self.obj.memoized_object)
        del self.obj.memoized_object
        self.assertIsNot(self.obj.memoized_object, sentinel)
        self.assertIsNot(self.obj.memoized_object, previous)

    def test_invalidated_memoized_object(self):
        previous = self.obj.memoized_object
        self.obj.invalidate_cache()
        self.assertIsNot(previous, self.obj.memoized_object)


class TestInheritedValue(TransactionCase):
    def setUp(self):
        super(TestInheritedValue, self).setUp()
        Value = self.Value = self.env["test.property.value"]
        Identifier = self.Identifier = self.env["test.property.inherits"]
        for i in range(10):
            val = Value.create({"thing": repr({i: i})})
            iden = Identifier.create({"name": "v%d" % i, "value_id": val.id})
            self.assertEqual(val.thing, iden.thing)
            self.assertEqual(iden.result, val.result)

    def test_result_write(self):
        i = self.Identifier.search([], limit=1)
        v = {"a": [1, (1, 2), "a"]}
        i.write({"result": v})
        self.assertEqual(i.thing, repr(v))

    def test_isinstance(self):
        TValue = type(self.env["test.property.value"])
        self.assertIsInstance(TValue.result, fields.Property)
        self.assertNotIsInstance(TValue.thing, fields.Property)

    def test_issubclass(self):
        TValue = type(self.env["test.property.value"])
        self.assertIsSubclass(type(TValue.result), fields.Property)
        self.assertNotIsSubclass(type(TValue.thing), fields.Property)

    def assertIsSubclass(self, subclass, superclass, msg=None):
        assert issubclass(
            subclass, superclass
        ), "{subclass} is not a subclass or {superclass}".format(
            subclass=subclass, superclass=superclass
        )

    def assertNotIsSubclass(self, subclass, superclass, msg=None):
        assert not issubclass(
            subclass, superclass
        ), "{subclass} is a subclass or {superclass}".format(
            subclass=subclass, superclass=superclass
        )
