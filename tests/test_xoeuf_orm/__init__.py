#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Copyright (c) Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can do what the LICENCE file allows you to.
#

from xoeuf import models, fields


class Node(models.Model):
    _name = "test_xoeuf_orm.node"
    parent = fields.Many2one(_name)
    children = fields.One2many(_name, "parent")
