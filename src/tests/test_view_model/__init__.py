#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Copyright (c) Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can do what the LICENCE file allows you to.
#
from xoeuf import api, fields, models
from odoo import exceptions

TEST_MODEL_NAME = "test_view_model.model"
TEST_MODEL_NAME2 = "test_view_model.model2"


class ExampleMixin(models.AbstractModel):
    _name = "example.mixin"

    is_example_mixin = True


class Model(models.Model):
    _name = TEST_MODEL_NAME

    name = fields.Char()
    value = fields.Integer()


ViewModel1 = models.ViewModel("view_model1", TEST_MODEL_NAME, mixins=["example.mixin"])


class ViewModel2(models.ViewModel("view_model2", TEST_MODEL_NAME)):
    @api.constrains("value")
    def check_value(self):
        for record in self:
            if record.value < 0:
                raise exceptions.ValidationError("value must be positive.")


class Model2(models.Model):
    _name = TEST_MODEL_NAME2

    ref_model = fields.Many2one(TEST_MODEL_NAME)
    model_value = fields.Integer(compute="get_model_value", store=True)

    @api.depends("ref_model", "ref_model.value")
    def get_model_value(self):
        for record in self:
            record.model_value = record.ref_model.value
