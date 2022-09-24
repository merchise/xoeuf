#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Copyright (c) Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can do what the LICENCE file allows you to.
#
from xotl.tools.future.codecs import safe_decode

from xoeuf.signals import (
    mock_replace,
    post_create,
    pre_create,
    write_wrapper,
    pre_fields_view_get,
    no_signals,
)

from odoo.tests.common import TransactionCase, at_install, post_install

# Don't import relatively
from odoo.addons.test_signals.models import (
    post_save_receiver,
    post_save_receiver_all_models,
    pre_save_receiver,
    wrap_nothing,
    pre_fvg_receiver,
)


@at_install(False)
@post_install(True)
class TestXoeufSignals(TransactionCase):
    def setUp(self):
        super(TestXoeufSignals, self).setUp()
        self.Model = self.env["test_signals.signaling_model"]
        self._ready_before = self.env.registry.ready
        self.env.registry.ready = True

    def tearDown(self):
        self.env.registry.ready = self._ready_before

    def test_post_create(self):
        with mock_replace(
            post_create, post_save_receiver
        ) as mock_post_create, mock_replace(
            pre_create, post_save_receiver
        ) as mock_pre_create:
            self.Model.create(dict(name="My name"))
            self.assertTrue(mock_post_create.called)
            self.assertFalse(mock_pre_create.called)

    def test_pre_create(self):
        with mock_replace(
            post_create, pre_save_receiver
        ) as mock_post_create, mock_replace(
            pre_create, pre_save_receiver
        ) as mock_pre_create:
            self.Model.create(dict(name="My name"))
            self.assertFalse(mock_post_create.called)
            self.assertTrue(mock_pre_create.called)

    def test_writer_wrap(self):
        def wrapper(sender, signal, *args, **kwargs):
            yield

        who = self.Model.create(dict(name="My name"))
        with mock_replace(write_wrapper, wrap_nothing, side_effect=wrapper) as mock:
            self.assertFalse(mock.called)
            who.write(dict(name="My new name"))
            self.assertTrue(mock.called)
        with mock_replace(write_wrapper, wrap_nothing, side_effect=wrapper) as mock:
            who.name = "My new other name"
            self.assertTrue(mock.called)

    def test_not_called_for_partners(self):
        with mock_replace(post_create, post_save_receiver) as mock, mock_replace(
            post_create, post_save_receiver_all_models
        ) as mock_all:
            partner = self.env["res.partner"].create(dict(name="Contact Info"))
            partner.email = "a@b.c"
            self.assertFalse(mock.called)
            self.assertTrue(mock_all.called)

    def test_fvg_in_abstract_models(self):
        who = self.Model.create(dict(name="My name"))
        with mock_replace(pre_fields_view_get, pre_fvg_receiver) as mock:
            result = who.fields_view_get()
            self.assertTrue(mock.called)
            self.assertIn("fgv-is-present", safe_decode(result["arch"], "utf-8"))

    def test_no_signals(self):
        # Test mocks outside and inside
        with mock_replace(pre_create, pre_save_receiver) as mock:
            with no_signals(pre_create):
                self.Model.create(dict(name="My name"))
            self.Model.create(dict(name="My name"))
            self.assertEqual(mock.call_count, 1)

        with no_signals(pre_create):
            with mock_replace(pre_create, pre_save_receiver) as mock:
                self.Model.create(dict(name="My name"))
                self.assertFalse(mock.called)

    def test_model_create_multi(self):
        with mock_replace(pre_create, pre_save_receiver) as mock:
            result = self.Model.create([dict(name="My name"), dict(name="Second obj")])
            # The mock is called once even though there are two records to
            # create.
            self.assertEqual(mock.call_count, 1)
            self.assertEqual(len(result), 2)
