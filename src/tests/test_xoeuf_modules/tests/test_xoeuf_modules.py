#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Copyright (c) Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can do what the LICENCE file allows you to.
#
from odoo.tests.common import BaseCase


class TestModules(BaseCase):
    def test_get_object_module(self):
        from .. import Foo
        from xoeuf.modules import get_object_module

        self.assertEqual(get_object_module(Foo), Foo.module)
