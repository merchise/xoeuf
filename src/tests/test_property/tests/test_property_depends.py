#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Copyright (c) Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can do what the LICENCE file allows you to.
#
from hypothesis import assume, given
from hypothesis import strategies as st
from odoo.addons.test_property.models import Undefined
from odoo.tests.common import TransactionCase

from xoeuf.testing.db import rollbacked

values = st.integers()


class TestPropertyDepends(TransactionCase):
    @given(values, values)
    @rollbacked
    def test_setting_property(self, value1, value2):
        assume(value1 != value2)
        Value = self.env["test.property.value"]
        obj = Value.create({})

        obj.price = value1
        self.assertEqual(obj.price_display, "$ {:.2f}".format(value1))

        # The test above won't actually fail because when doing obj.price the
        # value won't be in the cache, so Odoo will trigger the computation,
        # but if we change the value again, the Property must trigger the
        # recomputation itself:
        obj.price = value2
        self.assertEqual(obj.price_display, "$ {:.2f}".format(value2))

        obj.price = Undefined
        self.assertEqual(obj.price_display, "--")

    @given(values, values)
    @rollbacked
    def test_setting_dependant(self, value1, value2):
        Value = self.env["test.property.value"]
        obj = Value.create({})
        obj.price_display = "alsdkjfalsd"
        self.assertIs(obj.price, Undefined)

    @given(values, values)
    @rollbacked
    def test_setting_property_and_reading(self, value1, value2):
        assume(value1 != value2)
        Value = self.env["test.property.value"]
        obj = Value.create({})

        obj.price = value1
        self.assertEqual(obj.price_display, "$ {:.2f}".format(value1))

        # The test above won't actually fail because when doing obj.price the
        # value won't be in the cache, so Odoo will trigger the computation,
        # but if we change the value again, the Property must trigger the
        # recomputation itself:
        obj.price = value2
        price_display_stored = obj.read(("price_display_stored",))[0]["price_display_stored"]
        self.assertEqual(price_display_stored, "$ {:.2f}".format(value2))

        obj.price = Undefined
        price_display_stored = obj.read(("price_display_stored",))[0]["price_display_stored"]
        self.assertEqual(price_display_stored, "--")
