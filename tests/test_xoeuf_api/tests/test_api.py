#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Copyright (c) Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can do what the LICENCE file allows you to.
#
from odoo.tests.common import TransactionCase


class TestFromActiveIds(TransactionCase):
    # I don't really need to create records, since we're not reading anything
    # from the the DB

    def test_self_takes_from_active_ids(self):
        Model = self.env["xoeuf.tests.test_api.model"]
        res = Model.with_context(
            active_model=Model._name, active_ids=(1, 2, 3, 4)
        ).return_self_ids()
        self.assertEqual(res, [1, 2, 3, 4])

    def test_not_leaked_context(self):
        Model = self.env["xoeuf.tests.test_api.model"]
        this = Model.with_context(active_model=Model._name, active_ids=(1, 2, 3, 4))
        res, res2 = this.return_ids_and_call_method((5, 6), "return_self_ids")
        self.assertEqual(res, [1, 2, 3, 4])
        self.assertEqual(res2, [5, 6])

    def test_leaked_context(self):
        Model = self.env["xoeuf.tests.test_api.model"]
        this = Model.with_context(active_model=Model._name, active_ids=(1, 2, 3, 4))
        res, res2 = this.leaked_return_ids_and_call_method((5, 6), "return_self_ids")
        self.assertEqual(res, [1, 2, 3, 4])
        self.assertEqual(res2, res)

    def test_onupdate(self):
        user = self.env.user
        text_field = "text_field"

        # No onupdate method should be called
        user.text_field = text_field
        self.assertEqual(user.text_field, text_field)

        # ``update_text_field`` must be called
        user.name = "john doe"
        self.assertNotEqual(user.text_field, text_field)
        self.assertEqual(user.text_field, user.get_text_field())

        # ``update_text_field`` must be called
        user = user.create({"login": "new_user", "partner_id": user.partner_id.id})
        self.assertNotEqual(user.text_field, text_field)
        self.assertEqual(user.text_field, user.get_text_field())

        # ``update_text_field`` must be called replacing `text_field` creation value
        user = user.create(
            {
                "login": "new_user2",
                "partner_id": user.partner_id.id,
                "text_field": "text_field",
            }
        )
        self.assertNotEqual(user.text_field, text_field)
        self.assertEqual(user.text_field, user.get_text_field())

        # No onupdate method should be called
        text_field = user.text_field
        user.login = "jane doe"
        self.assertEqual(user.text_field, text_field)

        # ``update_text_field`` must be called
        partner = user.partner_id
        partner.name = "Admin"
        self.assertNotEqual(user.text_field, text_field)
        self.assertEqual(user.text_field, user.get_text_field())

        # No onupdate method should be called
        text_field = user.text_field
        partner.res = "Administrador"
        self.assertEqual(user.text_field, text_field)

    def test_onupdate_inherited_via_mixin(self):
        user = self.env.user
        obj = self.env["text.onupdate.big.model"].create({"user_id": user.id})
        user.name = name = "Johny"
        self.assertEqual(obj.name, "Updated: {name}".format(name=name))

    def test_onupdate_validate_fields(self):
        user = self.env.user
        # Just check we don't raise an exception.
        user._validate_fields("unknown_field_name_" + str(id(self)))
