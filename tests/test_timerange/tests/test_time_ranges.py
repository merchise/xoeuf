#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------
# Copyright (c) Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can do what the LICENCE file allows you to.
#
from datetime import datetime
from odoo.tests.common import TransactionCase

Hours = {"15:30": 15.5, "12:00": 12, "9:45": 9.75}


class TestTimeRange(TransactionCase):
    def setUp(self):
        super(TestTimeRange, self).setUp()
        self.Model = self.env["test.time.range"]

    def test_compute_range(self):
        obj = self.Model.create(dict(time_value=Hours["15:30"]))

        self.assertEqual(obj.range_value, "afternoon")

        obj.time_value = Hours["9:45"]

        self.assertEqual(obj.range_value, "morning")

        obj.time_value = Hours["12:00"]

        self.assertEqual(obj.range_value, "noon")

    def test_compute_datetime_range_by_tzone(self):
        obj = self.Model.create(dict(datetime_value=datetime(2020, 8, 31, 12, 0, 0)))

        self.assertEqual(obj.range_datetime, "noon")

        obj.tz = "America/Havana"

        self.assertEqual(obj.range_datetime, "morning")
