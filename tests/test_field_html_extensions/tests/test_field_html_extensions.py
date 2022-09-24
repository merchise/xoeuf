#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Copyright (c) Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can do what the LICENCE file allows you to.
#
from xoeuf import fields

from odoo.tests.common import TransactionCase


class TestLocalizedDt(TransactionCase):
    def setUp(self):
        super().setUp()
        self.valid_html = self.env["test_field_html_extensions.model"].create(
            {"html": "<p>This is ok</p>"}
        )
        self.empty_html = self.env["test_field_html_extensions.model"].create(
            {"html": ""}
        )
        self.empty_html_with_tags = self.env["test_field_html_extensions.model"].create(
            {"html": "<p> &nbsp;</p>"}
        )
        self.empty_html_with_br = self.env["test_field_html_extensions.model"].create(
            {"html": "<p><br/></p>"}
        )

    def test_valid_html_non_empty_record_signature(self):
        field = self.valid_html._fields["html"]
        self.assertEqual(field.extract_text(self.valid_html), "This is ok")
        self.assertFalse(field.is_plain_text_empty(self.valid_html))

    def test_valid_html_non_empty_recordless_signature(self):
        self.assertEqual(fields.Html.extract_text(self.valid_html.html), "This is ok")
        self.assertFalse(fields.Html.is_plain_text_empty(self.valid_html.html))

    def test_valid_empty_html_without_tags_record_signature(self):
        field = self.valid_html._fields["html"]
        self.assertEquals(field.extract_text(self.empty_html), "")
        self.assertTrue(field.is_plain_text_empty(self.empty_html))

    def test_valid_empty_html_without_tags_recordless_signature(self):
        self.assertEquals(fields.Html.extract_text(self.empty_html.html), "")
        self.assertTrue(fields.Html.is_plain_text_empty(self.empty_html.html))

    def test_valid_empty_with_br_record_signature(self):
        field = self.valid_html._fields["html"]
        self.assertEquals(field.extract_text(self.empty_html_with_br), "")
        self.assertIsNot(field.is_plain_text_empty(self.empty_html_with_br), None)
        self.assertTrue(field.is_plain_text_empty(self.empty_html_with_br))

    def test_valid_empty_with_br_recordless_signature(self):
        self.assertEquals(fields.Html.extract_text(self.empty_html_with_br.html), "")
        self.assertIsNot(
            fields.Html.is_plain_text_empty(self.empty_html_with_br.html), None
        )
        self.assertTrue(fields.Html.is_plain_text_empty(self.empty_html_with_br.html))
