#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Copyright (c) Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can do what the LICENCE file allows you to.
#
from odoo.tests.common import TransactionCase

from xoeuf.models.extensions import get_ref


class TestModels(TransactionCase):
    def test_get_ref(self):
        Foo = self.env["test_xoeuf_models.foobar"]
        record = self.env.ref("test_models.record1")
        self.assertEqual(record, get_ref(Foo, "record1"))
        self.assertEqual(record, Foo.get_ref("record1"))

    def test_iter_descendant_models(self):
        Top = self.env["test_xoeuf_models.top"]
        Middleware = self.env["test_xoeuf_models.middleware"]
        Foo = self.env["test_xoeuf_models.foobar"]
        Baz = self.env["test_xoeuf_models.baz"]
        Linked = self.env["test_xoeuf_models.linked"]
        Delegated = self.env["test_xoeuf_models.delegated"]
        Relinked = self.env["test_xoeuf_models.relinked"]
        self.assertEqual(
            set(Top.iter_descendant_models(find_delegated=False)),
            set([(Foo._name, Foo)]),
        )
        self.assertEqual(
            set(Top.iter_descendant_models()),
            set(
                [
                    (Foo._name, Foo),
                    (Linked._name, Linked),
                    (Delegated._name, Delegated),
                    (Relinked._name, Relinked),
                ]
            ),
        )
        self.assertEqual(set(Top.iter_descendant_models(find_inherited=False)), set([]))
        self.assertEqual(
            set(Foo.iter_descendant_models(find_inherited=False)),
            set(
                [
                    (Linked._name, Linked),
                    (Delegated._name, Delegated),
                    (Relinked._name, Relinked),
                ]
            ),
        )
        self.assertEqual(
            set(Top.iter_descendant_models(find_delegated=False, allow_transient=True)),
            set([(Foo._name, Foo), (Baz._name, Baz)]),
        )
        self.assertEqual(
            set(Top.iter_descendant_models(find_delegated=False, allow_abstract=True)),
            set([(Foo._name, Foo), (Middleware._name, Middleware)]),
        )
