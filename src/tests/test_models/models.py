#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Copyright (c) Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can do what the LICENCE file allows you to.
#
from xoeuf import api, fields, models
from xoeuf.models.extensions import get_ref


class Top(models.AbstractModel):
    _name = "test_xoeuf_models.top"


class Middleware(models.AbstractModel):
    _name = "test_xoeuf_models.middleware"
    _inherit = [Top._name]


class FooBar(models.Model):
    _name = "test_xoeuf_models.foobar"
    _inherit = [Middleware._name]

    name = fields.Text()

    @api.model
    def get_ref(self, ref):
        return get_ref(self, ref)


class Baz(models.TransientModel):
    _name = "test_xoeuf_models.baz"
    _inherit = [Middleware._name]


class Linked(models.Model):
    _name = "test_xoeuf_models.linked"
    _inherits = {FooBar._name: "foobar"}


class Delegated(models.Model):
    _name = "test_xoeuf_models.delegated"

    foobar = fields.Many2one(FooBar._name, delegate=True)


class Relinked(models.Model):
    _name = "test_xoeuf_models.relinked"

    foobar = fields.Many2one(Delegated._name, delegate=True)
