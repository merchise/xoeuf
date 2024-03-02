#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Copyright (c) Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can do what the LICENCE file allows you to.
#
from xoeuf import models, fields


class A(models.Model):
    _name = "test.one2one.a"
    name = fields.Char()


class B(models.Model):
    _name = "test.one2one.b"
    _inherits = {"test.one2one.a": "a_id"}


class Mixin(models.AbstractModel):
    _name = "test.one2one.mixin"

    set_null = fields.One2one(B._name, ondelete="set null")


class C(models.Model):
    _name = "test.one2one.c"
    _inherit = [Mixin._name]
    _inherits = {"test.one2one.a": "a_id"}

    a_id = fields.One2one("test.one2one.a")


class D(models.Model):
    _name = "test.one2one.d"
    _inherits = {"test.one2one.c": "c_id"}
