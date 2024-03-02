#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Copyright (c) Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can do what the LICENCE file allows you to.
#
from odoo.tests.common import TransactionCase


class TestORMSymbolsInXML(TransactionCase):
    def test_nodes_were_created(self):
        parent = self.env.ref("test_xoeuf_orm.parent_node")
        self.assertEqual(len(parent.children), 2)
