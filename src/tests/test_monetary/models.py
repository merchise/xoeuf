#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Copyright (c) Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can do what the LICENCE file allows you to.
#
from xoeuf import models, fields


class Line(models.Model):
    _name = "test.monetary.line"
    value = fields.Monetary()
    currency_id = fields.Many2one("res.currency")


class ConcreteLine(models.Model):
    _name = "test.monetary.concrete"
    value = fields.Monetary(concrete=True)
    currency_id = fields.Many2one("res.currency")


class RelatedLine(models.Model):
    _name = "test.monetary.related"
    value = fields.Monetary(concrete=True)
    company_id = fields.Many2one("res.company")
    currency_id = fields.Many2one(related="company_id.currency_id")
