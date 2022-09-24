#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Copyright (c) Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can do what the LICENCE file allows you to.
#
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestViewModel(TransactionCase):
    def test_view_model_module(self):
        self.assertEqual(self.env["view_model1"]._module, "test_view_model")
        self.assertEqual(self.env["view_model2"]._module, "test_view_model")

    def test_mixins(self):
        is_example_mixin = lambda model_name: getattr(
            self.env[model_name], "is_example_mixin", False
        )
        self.assertTrue(is_example_mixin("view_model1"))
        self.assertFalse(is_example_mixin("view_model2"))
        self.assertFalse(is_example_mixin("test_view_model.model"))

    def test_non_shared_extensions(self):
        view1 = self.env["view_model1"]
        view2 = self.env["view_model2"]
        values = {"name": "x", "value": -10}
        self.assertTrue(view1.create(values))
        self.assertRaises(ValidationError, view2.create, values)

    def test_depends(self):
        model1 = self.env["test_view_model.model"]
        model2 = self.env["test_view_model.model2"]
        view2 = self.env["view_model1"]
        values = {"name": "x", "value": -10}
        obj1 = model1.create(values)
        obj2 = model2.create({"ref_model": obj1.id})
        model1.invalidate_cache()
        model2.invalidate_cache()
        self.assertEqual(obj1.value, obj2.model_value)
        obj1.value = 3
        model1.invalidate_cache()
        model2.invalidate_cache()
        self.assertEqual(obj1.value, obj2.model_value)
        view2.browse(obj1.id).value = 7
        model1.invalidate_cache()
        model2.invalidate_cache()
        self.assertNotEqual(obj1.value, obj2.model_value)
