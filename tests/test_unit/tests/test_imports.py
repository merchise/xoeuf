#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Copyright (c) Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can do what the LICENCE file allows you to.
#
from odoo.tests.common import BaseCase


class TestXoeufImports(BaseCase):
    def test_xoeuf_imports(self):
        "Xoeuf is importable in Python 2 and 3"
        from xoeuf import fields, models, api  # noqa

        try:
            from xoeuf.fields import Serialized  # noqa
        except ImportError:
            pass
        else:
            assert False, "Serialized should not be exported"
