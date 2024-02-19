#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Copyright (c) Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can do what the LICENCE file allows you to.
#
from psycopg2 import IntegrityError
from odoo.tests.common import TransactionCase


class TestO2O(TransactionCase):
    def test_one2one_injects_restriction(self):
        C = self.env["test.one2one.c"]
        c = C.create({"name": "I am a C"})
        a = c.a_id
        with self.assertRaises(IntegrityError):
            C.create({"name": "I am trying to steal the A", "a_id": a.id})

    def test_one2one_baseline(self):
        B = self.env["test.one2one.b"]
        b = B.create({"name": "I am a B"})
        a = b.a_id
        B.create({"name": "I can steal the A", "a_id": a.id})

    def test_one2one_cascade(self):
        C = self.env["test.one2one.c"]
        c = C.create({"name": "I am a C"})
        a = c.a_id
        a.unlink()
        self.assertFalse(c.exists())

    def test_one2one_related(self):
        D = self.env["test.one2one.d"]
        d = D.create({"name": "I am a D"})
        a = d.a_id
        with self.assertRaises(IntegrityError):
            D.create({"name": "I am trying to steal the A", "a_id": a.id})

    def test_one2one_doesnt_lose_ondelete(self):
        C = self.env["test.one2one.c"]
        set_null = C._fields["set_null"]
        a_id = C._fields["a_id"]
        self.assertEqual(a_id.ondelete, "cascade")
        self.assertEqual(set_null.ondelete, "set null")
