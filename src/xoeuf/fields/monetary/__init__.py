#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Copyright (c) Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can do what the LICENCE file allows you to.
#
from odoo.fields import Monetary as Base


class Monetary(Base):
    """A monetary field.

    This is the same as Odoo's original `odoo.fields.Monetary`:class:, with an
    additional attribute:

    :param concrete: If set to True record-set will return the value as a `concrete
                     monetary value <xotl.tools.dim.currencies>`:mod:.  Which means you
                     can only operate it with commensurable monetary values.

    """

    _slots = {"concrete": False}

    # Putting the concrete quantity in the cache (i.e implementing the
    # convert_to_cache) may lead to unwanted type errors (TypeError:
    # incomparable quantities: 0.0::{EUR}/{} and 0) when rounding the value in
    # the cache.  So the best approach is just to override the __get__ of the
    # descriptor.
    def __get__(self, instance, owner):
        from xotl.tools.dim.currencies import currency as Currency

        result = super(Monetary, self).__get__(instance, owner)
        if instance and self.concrete:
            result *= Currency(instance[self.currency_field].name)
        return result
