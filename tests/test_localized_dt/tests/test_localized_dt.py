#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Copyright (c) Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can do what the LICENCE file allows you to.
#
import unittest
from odoo.tests.common import TransactionCase


class TestLocalizedDt(TransactionCase):
    @unittest.expectedFailure
    def test_getting_the_field(self):
        obj = self.env["test_localizated_dt.model"].create(
            {"dt_at_tzone": "2018-01-01 12:00:00"}
        )
        # 12M on January (no DTS) in Cuba is -5 hours from UTC
        self.assertEqual(obj.dt, "2018-01-01 17:00:00")
