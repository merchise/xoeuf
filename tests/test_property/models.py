#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Copyright (c) Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can do what the LICENCE file allows you to.
#
import logging
import numbers
import pickle

from xoeuf import models, fields, api
from odoo.tools.safe_eval import safe_eval

logger = logging.getLogger(__name__)
del logging


class _Undefined:
    _instance = None

    def __new__(cls):
        if cls._instance is not None:
            return cls._instance
        else:
            res = cls._instance = super().__new__(cls)
            return res


Undefined = _Undefined


class PriceMixin(models.AbstractModel):
    _name = "test.property.pricemixin"

    # We'll store the pickled value in the DB; the true value is in the price
    # Property and a user-friendly repr in the price field.
    _db_price = fields.Binary()

    @fields.Property
    def price(self):
        if self._db_price:
            return pickle.loads(self._db_price)
        else:
            return Undefined

    @price.setter
    def price(self, value):
        if isinstance(value, numbers.Number):
            self._db_price = pickle.dumps(value)
        else:
            self._db_price = None

    price_display = fields.Char(compute="_compute_price", inverse="_set_price")
    price_display_stored = fields.Char(
        compute="_compute_price", inverse="_set_price", store=True
    )

    @api.one
    @api.depends("price")
    def _compute_price(self):
        if self.price is Undefined:
            self.price_display = "--"
            self.price_display_stored = "--"
        else:
            self.price_display = "$ {:.2f}".format(self.price)
            self.price_display_stored = "$ {:.2f}".format(self.price)

    def _set_price(self):
        user_price = self.price_display.strip()
        if user_price and user_price != "--" and user_price[0] in "$01234567890.":
            if user_price[0] == "$":
                user_price = user_price[1:].strip()
            try:
                if "." in user_price:
                    self.price = float(user_price)
                else:
                    self.price = int(user_price)
            except ValueError:
                self.price = Undefined


class ValueMixin(models.AbstractModel):
    _name = "test.property.valuemixin"

    value = fields.Char()

    @fields.Property
    def inverted(self):
        return "".join(reversed(self.value)) if self.value else self.value

    @inverted.setter
    def inverted(self, value):
        self.value = "".join(reversed(value)) if value else value

    @inverted.deleter
    def inverted(self):
        self.value = None

    @inverted.onsetup
    def inverted(field, model):
        type(model).inverted_setup = True

    @fields.Property(memoize=True)
    def memoized_object(self):
        return object()

    @memoized_object.setter
    def memoized_object(self, value):
        pass

    @memoized_object.deleter
    def memoized_object(self):
        pass

    @fields.Property
    def new_object(self):
        return object()


class ObjectMixin(models.AbstractModel):
    _name = "test.property.object"

    thing = fields.Char(
        # This stores the representation (result of repr) of the value.  You
        # may use `result` to read/update this field.  If you use Odoo's
        # write/create, or set this field directly you MUST ensure to pass the
        # result of `repr()`.  The `write/create` methods below ensure the
        # writing to 'result' works.
    )

    @api.multi
    def write(self, values):
        # Makes writing to 'result' work.  If you pass both 'value' and
        # 'result', 'result' wins.
        if "result" in values:
            values["thing"] = repr(values.pop("result"))
        return super(ObjectMixin, self).write(values)

    @api.model
    def create(self, values):
        # Makes writing to 'result' work.  If you pass both 'value' and
        # 'result', 'result' wins.
        if "result" in values:
            values["thing"] = repr(values.pop("result"))
        return super(ObjectMixin, self).create(values)

    def _get_result(self):
        return safe_eval(self.thing) if self.thing else self.thing

    def _set_result(self, value):
        self.thing = repr(value)

    def _del_result(self):
        self.thing = None

    result = fields.Property(
        getter=_get_result, setter=_set_result, deleter=_del_result
    )
    del _get_result, _set_result, _del_result


class Value(models.Model):
    _name = "test.property.value"
    _inherit = [ValueMixin._name, ObjectMixin._name, PriceMixin._name]


class IdentifiedValue(models.Model):
    _name = "test.property.inherits"
    _inherits = {"test.property.value": "value_id"}

    name = fields.Char(required=True)
    value_id = fields.Many2one("test.property.value", required=True, ondelete="cascade")

    _sql_constrains = [
        ("unique_name", "UNIQUE(name)", "Names cannot be repeated"),
        ("single_value", "UNIQUE(value_id)", "A value can only appear once"),
    ]


class DelegatedValue(models.Model):
    _name = "test.property.delegated"
    name = fields.Char(required=True)
    value_id = fields.Many2one(
        "test.property.value", required=True, ondelete="cascade", delegate=True
    )

    _sql_constrains = [
        ("unique_name", "UNIQUE(name)", "Names cannot be repeated"),
        ("single_value", "UNIQUE(value_id)", "A value can only appear once"),
    ]
