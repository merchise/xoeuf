#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Copyright (c) Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can do what the LICENCE file allows you to.
#
from xoeuf import models, fields


class DomainModel(models.Model):
    _name = "test_domain.model"

    name = fields.Text()
    age = fields.Integer()

    parent_id = fields.Many2one(_name)
    children_ids = fields.One2many(_name, "parent_id")

    def __repr__(self):
        def _repr(rec):
            return "{id}({name!r}, {age!r}, {children!r})".format(
                id=rec.id, name=rec.name, age=rec.age, children=rec.children_ids
            )

        recs = "; ".join(_repr(r) for r in self)
        return "{{{0}}}".format(recs)
