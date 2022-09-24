#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Copyright (c) Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can do what the LICENCE file allows you to.
#
from collections import Mapping
from enum import IntEnum, Enum
from xoeuf import api, models, fields


class COLORS(IntEnum):
    Blue = 0
    Red = 1
    Green = 2


class CARS(Enum):
    FORD = object()
    CHEV = object()


class Pax(object):
    single = 1
    double = 2
    __members__ = {"single": single, "double": double}


class WorkType(int):
    pass


class WORK_TYPE(object):
    easy = WorkType(0)
    hard = WorkType(1)
    __members__ = {"easy": easy, "hard": hard}


class Mixin(models.AbstractModel):
    _name = "test_enumeration.mixin"
    color = fields.Enumeration(COLORS, default=COLORS.Red)
    color_name = color.get_selection_field("color", "color_name")
    # color_rgb = fields.Char(compute="_compute_color_rgb")
    # color_rgb2 = fields.Char(compute="_compute_color_rgb", store=True)

    # def _compute_color_rgb(self):
    #     for record in self:
    #         if record.color_name == "Red":
    #             record.color_rgb = "#f00"
    #         elif record.color_name == "Blue":
    #             record.color_rgb = "#00f"
    #         elif record.color_name == "Green":
    #             record.color_rgb = "#0f0"
    #         else:
    #             record.color_rgb = "#fff"


class Model(models.Model):
    _name = "test.enum.model"
    _inherit = ["test_enumeration.mixin"]

    car = fields.Enumeration(CARS)
    pax = fields.Enumeration(Pax)

    def _get_enumclass(self):
        if self._name == "test.enum.model_delegated":

            class Dynamic(Enum):
                name = "Dynamic"

        else:

            class Dynamic(Enum):
                name = "Static"

        return Dynamic

    dynamic_enum = fields.Enumeration(_get_enumclass)


class DelegatedModel(models.Model):
    _name = "test.enum.model_delegated"
    _inherits = {"test.enum.model": "model_id"}

    model_id = fields.Many2one("test.enum.model")

    @api.model_create_multi
    def create(self, values):
        if isinstance(values, Mapping):
            values = self._pre_create_model_id(values)
        else:
            values = [self._pre_create_model_id(vals) for vals in values]
        return super(DelegatedModel, self).create(values)

    @api.model
    def _pre_create_model_id(self, values):
        if "model_id" not in values:
            values["model_id"] = self.env["test.enum.model"].create({}).id
        return values
