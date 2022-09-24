#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Copyright (c) Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can do what the LICENCE file allows you to.
#
from datetime import timedelta
from hypothesis import strategies, given

from odoo.tests.common import TransactionCase


timedeltas = strategies.timedeltas()
ALMOST_A_SECOND = timedelta(seconds=1, microseconds=-0.0001)


class TestTimedelta(TransactionCase):
    def setUp(self):
        super(TestTimedelta, self).setUp()
        self.Value = self.env["test.timedelta.value"]

    @given(timedeltas)
    def test_create(self, value):
        obj = self.Value.create({"delta": value})
        id = obj.id
        self.Value.invalidate_cache()
        obj = self.Value.browse(id)
        self.assertAlmostEqual(obj.delta, value, delta=ALMOST_A_SECOND)

    @given(timedeltas)
    def test_create2(self, value):
        obj = self.Value.create({"delta": value.total_seconds()})
        id = obj.id
        self.Value.invalidate_cache()
        obj = self.Value.browse(id)
        self.assertIsInstance(obj.delta, timedelta)
        self.assertAlmostEqual(obj.delta, value, delta=ALMOST_A_SECOND)

    @given(timedeltas)
    def test_set(self, value):
        obj = self.Value.create({})
        obj.delta = value
        id = obj.id
        self.Value.invalidate_cache()
        obj = self.Value.browse(id)
        self.assertAlmostEqual(obj.delta, value, delta=ALMOST_A_SECOND)

    @given(timedeltas)
    def test_set2(self, value):
        obj = self.Value.create({})
        obj.delta = value.total_seconds()
        id = obj.id
        self.Value.invalidate_cache()
        obj = self.Value.browse(id)
        self.assertIsInstance(obj.delta, timedelta)
        self.assertAlmostEqual(obj.delta, value, delta=ALMOST_A_SECOND)
