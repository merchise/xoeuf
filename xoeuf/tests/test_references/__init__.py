#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Copyright (c) Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can do what the LICENCE file allows you to.
#
from xoeuf import fields, models, api

MIXIN_NAME = "example.mixin"


class ExampleMixin(models.AbstractModel):
    _name = MIXIN_NAME

    test = fields.Char(default="Hello")
    partner_id = fields.Many2one("res.partner")


class Model1(models.Model):
    _name = "test.model1"
    _inherit = MIXIN_NAME
    _description = "Model 1"


class Model2(models.Model):
    _name = "test.model2"
    _inherit = MIXIN_NAME


class SubModel2(models.Model):
    _name = "test.sub.model2"
    _inherit = "test.model2"


class TestModel(models.Model):
    _name = "test.model"

    typed_ref = fields.TypedReference(mixin=MIXIN_NAME, delegate=True)
    filtered_typed_ref = fields.TypedReference(
        mixin=MIXIN_NAME, selection=[("test.model2", "model2")]
    )
