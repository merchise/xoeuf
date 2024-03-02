#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Copyright (c) Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can do what the LICENCE file allows you to.
#
from xoeuf import fields, models, api

MIXIN_NAME = "typed.reference.example.mixin"


class ExampleMixin(models.AbstractModel):
    _name = MIXIN_NAME

    test = fields.Char(default="Hello")
    partner_id = fields.Many2one("res.partner")
    test2 = fields.Char(default="Hello")
    name = fields.Char(related="partner_id.name", readonly=False)
    comment = fields.Text(related="partner_id.comment", readonly=False)
    ref = fields.Char(related="partner_id.ref", store=True, readonly=False)
    street = fields.Char(related="partner_id.street", store=True, readonly=False)
    phone = fields.Char(related="partner_id.phone", readonly=False)
    mobile = fields.Char(related="partner_id.mobile", readonly=False)


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
    # define to set store=True
    test2 = fields.Char(compute="_compute_test2", store=True)
    # name = fields.Char(compute="_compute_name", store=True)
    ref = fields.Char(compute="_compute_ref", store=True)

    @api.one
    @api.depends("typed_ref", "typed_ref.test2")
    def _compute_test2(self):
        if self.typed_ref:
            self.test2 = self.typed_ref.test2

    # @api.one
    # @api.depends("typed_ref", "typed_ref.partner_id.name")
    # def _compute_name(self):
    #     if self.typed_ref:
    #         self.name = self.typed_ref.name

    @api.one
    @api.depends("typed_ref", "typed_ref.ref")
    def _compute_ref(self):
        if self.typed_ref:
            self.ref = self.typed_ref.ref
