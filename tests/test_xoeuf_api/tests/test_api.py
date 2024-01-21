#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Copyright (c) Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can do what the LICENCE file allows you to.
#
from odoo.tests.common import TransactionCase


class TestFromActiveIds(TransactionCase):
    # I don't really need to create records, since we're not reading anything
    # from the the DB

    def test_self_takes_from_active_ids(self):
        Model = self.env["xoeuf.tests.test_api.model"]
        res = Model.with_context(
            active_model=Model._name, active_ids=(1, 2, 3, 4)
        ).return_self_ids()
        self.assertEqual(res, [1, 2, 3, 4])

    def test_not_leaked_context(self):
        Model = self.env["xoeuf.tests.test_api.model"]
        this = Model.with_context(active_model=Model._name, active_ids=(1, 2, 3, 4))
        res, res2 = this.return_ids_and_call_method((5, 6), "return_self_ids")
        self.assertEqual(res, [1, 2, 3, 4])
        self.assertEqual(res2, [5, 6])

    def test_leaked_context(self):
        Model = self.env["xoeuf.tests.test_api.model"]
        this = Model.with_context(active_model=Model._name, active_ids=(1, 2, 3, 4))
        res, res2 = this.leaked_return_ids_and_call_method((5, 6), "return_self_ids")
        self.assertEqual(res, [1, 2, 3, 4])
        self.assertEqual(res2, res)
