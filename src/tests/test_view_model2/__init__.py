#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Copyright (c) Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can do what the LICENCE file allows you to.
#
from xoeuf import fields, models
from odoo.addons.test_view_model import TEST_MODEL_NAME


class Model(models.Model):
    _inherit = TEST_MODEL_NAME

    new_value = fields.Float()
