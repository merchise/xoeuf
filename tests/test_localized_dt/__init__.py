#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Copyright (c) Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can do what the LICENCE file allows you to.
#
from xoeuf import fields, models


class Mixin(models.AbstractModel):
    _name = "test_localized_dt.mixin"

    tzone = fields.Char(default="America/Havana")
    dt = fields.Datetime()
    dt_at_tzone = fields.LocalizedDatetime("dt", "tzone")


class ModelA(models.Model):
    _name = "test_localizated_dt.model"
    _inherit = ["test_localized_dt.mixin"]


class ModelB(models.Model):
    _name = "test_localized_dt.inherited"
    _inherits = {models.get_modelname(ModelA): "a_id"}
