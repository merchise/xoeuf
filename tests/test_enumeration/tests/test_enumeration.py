#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Copyright (c) Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can do what the LICENCE file allows you to.
#
import contextlib

from hypothesis import strategies as s, given

from xoeuf import fields
from odoo.tests.common import TransactionCase, at_install, post_install

from ..models import COLORS, Pax, CARS, WORK_TYPE

colors = s.sampled_from(list(COLORS.__members__.values()))
color_pairs = s.sampled_from(list(COLORS.__members__.items()))
cars = s.sampled_from(list(CARS.__members__.values()))
paxs = s.sampled_from(list(Pax.__members__.values()))
wtypes = s.sampled_from(list(WORK_TYPE.__members__.values()))


@at_install(False)
@post_install(True)
class TestEnum(TransactionCase):
    def setUp(self):
        super(TestEnum, self).setUp()
        self.EnumModel = self.env["test.enum.model"]
        self.DelegatedModel = self.env["test.enum.model_delegated"]

    def test_column_type_force_char_columns(self):
        self.assertIsInstance(self.EnumModel._fields["color"], fields.Char)
        self.assertIsInstance(self.EnumModel._fields["color_name"], fields.Selection)

    def test_can_set_valid_integers(self):
        with force_ready(self.env.registry):
            obj = self.EnumModel.create({"color": 1, "car": CARS.FORD, "pax": 1})
        id = obj.id
        self.EnumModel.invalidate_cache()
        obj = self.EnumModel.browse(id)
        assert obj.color == COLORS.Red, "%r == %r" % (obj.color, COLORS.Red)
        assert obj.car is CARS.FORD
        assert obj.pax == 1
        # assert obj.color_rgb == obj.color_rgb2 == "#f00"

    @given(colors)
    def test_can_set_valid_values(self, color):
        with force_ready(self.env.registry):
            obj = self.EnumModel.create({"color": color})
        id = obj.id
        self.EnumModel.invalidate_cache()
        obj = self.EnumModel.browse(id)
        assert obj.color == color, "%r == %r" % (obj.color, color)

    @given(colors)
    def test_can_set_valid_values_as_integers_and_get_values(self, color):
        with force_ready(self.env.registry):
            obj = self.EnumModel.create({"color": int(color)})
        id = obj.id
        self.EnumModel.invalidate_cache()
        obj = self.EnumModel.browse(id)
        assert obj.color == color, "%r == %r" % (obj.color, color)
        assert isinstance(obj.color, COLORS)

    def test_cannot_set_invalid_integers(self):
        # Sinces tests are run while the registry is being populated, i.e not
        # ready, we need to trick it to allow receivers be executed.
        with force_ready(self.env.registry), self.assertRaises(ValueError):
            self.EnumModel.create({"color": 10})

    def test_cannot_write_invalid_integers(self):
        with force_ready(self.env.registry):
            obj = self.EnumModel.create({"color": 1})
            with self.assertRaises(ValueError):
                obj.write({"color": 10})

    def test_cannot_write_invalid_values(self):
        obj = self.EnumModel.create({"car": CARS.FORD})
        with force_ready(self.env.registry), self.assertRaises(ValueError):
            obj.write({"car": "any other brand"})

    def test_search_non_integer(self):
        self.EnumModel.search([]).unlink()
        with force_ready(self.env.registry):
            obj = self.EnumModel.create({"car": CARS.FORD})
            self.EnumModel.invalidate_cache()
            self.assertEqual(self.EnumModel.search([("car", "=", CARS.FORD)]), obj)
            self.assertEqual(
                self.EnumModel.search([("car", "=", CARS.CHEV)], count=True), 0
            )
            self.assertEqual(
                self.EnumModel.search([("car", "in", (CARS.FORD, CARS.CHEV))]), obj
            )
            with self.assertRaises(ValueError):
                self.EnumModel.search([("car", "=", 1)])

    def test_performance(self):
        from xoeuf.fields.enumeration import EnumerationAdapter

        self.assertIn(EnumerationAdapter, type(self.EnumModel).mro())
        self.assertNotIn(EnumerationAdapter, type(self.env["res.partner"]).mro())

    def test_search_integer(self):
        self.EnumModel.search([]).unlink()
        with force_ready(self.env.registry):
            obj = self.EnumModel.create({"color": COLORS.Red})
            self.EnumModel.invalidate_cache()
            self.assertEqual(self.EnumModel.search([("color", "=", 1)]), obj)
            with self.assertRaises(ValueError):
                self.EnumModel.search([("color", "=", 10)])

    def test_color_default_value(self):
        with force_ready(self.env.registry):
            obj = self.EnumModel.create({})
            self.assertEqual(obj.color, COLORS.Red)

    def test_color_computed_field_read(self):
        with force_ready(self.env.registry):
            obj = self.EnumModel.create({"color": COLORS.Red})
            self.assertEqual(obj.color_name, "Red")

    @given(color_pairs, color_pairs)
    def test_color_computed_field_set_on_create(self, pair, update):
        with force_ready(self.env.registry):
            name, value = pair
            obj = self.EnumModel.create({"color_name": name})
            self.assertEqual(obj.color, value)
            name, value = update
            obj = self.EnumModel.create({"color_name": name})
            self.assertEqual(obj.color, value)
        with force_ready(self.env.registry):
            name, value = pair
            obj = self.EnumModel.create({"color": value})
            self.assertEqual(obj.color_name, name)
            name, value = update
            obj = self.EnumModel.create({"color": value})
            self.assertEqual(obj.color_name, name)

    @given(color_pairs, color_pairs)
    def test_color_computed_field_set_on_assignment(self, pair, update):
        with force_ready(self.env.registry):
            name, value = pair
            obj = self.EnumModel.create({})
            obj.color_name = name
            self.assertEqual(obj.color, value)
            name, value = update
            obj.color_name = name
            self.assertEqual(obj.color, value)
        with force_ready(self.env.registry):
            name, value = pair
            obj = self.EnumModel.create({})
            obj.color = value
            self.assertEqual(obj.color_name, name)
            name, value = update
            obj.color = name
            self.assertEqual(obj.color_name, name)

    @given(color_pairs, color_pairs)
    def test_color_computed_field_set_on_write(self, pair, update):
        with force_ready(self.env.registry):
            name, value = pair
            obj = self.EnumModel.create({})
            obj.write({"color_name": name})
            self.assertEqual(obj.color, value)
            name, value = update
            obj = self.EnumModel.create({})
            obj.write({"color_name": name})
            self.assertEqual(obj.color, value)
        with force_ready(self.env.registry):
            name, value = pair
            obj = self.EnumModel.create({})
            obj.write({"color": value})
            self.assertEqual(obj.color_name, name)
            name, value = update
            obj = self.EnumModel.create({})
            obj.write({"color": value})
            self.assertEqual(obj.color_name, name)

    @given(color_pairs, color_pairs)
    def test_color_computed_field_set_on_create_delegated(self, pair, update):
        with force_ready(self.env.registry):
            name, value = pair
            obj = self.DelegatedModel.create({"color_name": name})
            self.assertEqual(obj.color, value)
            name, value = update
            obj = self.DelegatedModel.create({"color_name": name})
            self.assertEqual(obj.color, value)
        with force_ready(self.env.registry):
            name, value = pair
            obj = self.DelegatedModel.create({"color": value})
            self.assertEqual(obj.color_name, name)
            name, value = update
            obj = self.DelegatedModel.create({"color": value})
            self.assertEqual(obj.color_name, name)

    @given(color_pairs, color_pairs)
    def test_color_computed_field_set_on_assignment_delegated(self, pair, update):
        with force_ready(self.env.registry):
            name, value = pair
            obj = self.DelegatedModel.create({})
            obj.color_name = name
            self.assertEqual(obj.color, value)
            name, value = update
            obj.color_name = name
            self.assertEqual(obj.color, value)
        with force_ready(self.env.registry):
            name, value = pair
            obj = self.DelegatedModel.create({})
            obj.color = value
            self.assertEqual(obj.color_name, name)
            name, value = update
            obj.color = name
            self.assertEqual(obj.color_name, name)

    @given(color_pairs, color_pairs)
    def test_api_model_create_multi(self, pair1, pair2):
        name1, value1 = pair1
        name2, value2 = pair2
        with force_ready(self.env.registry):
            objs = self.DelegatedModel.create([{"color": value1}, {"color": value2}])
            self.assertEqual(set(objs.mapped("color_name")), {name1, name2})

    def test_dynamic_enumclass(self):
        Enumclass = self.EnumModel._fields["dynamic_enum"].Enumclass
        self.assertEqual(Enumclass.name.value, "Static")

        Enumclass = self.DelegatedModel._fields["dynamic_enum"].Enumclass
        self.assertEqual(Enumclass.name.value, "Dynamic")


@contextlib.contextmanager
def force_ready(registry):
    ready = registry.ready
    registry.ready = True
    try:
        yield
    finally:
        registry.ready = ready
