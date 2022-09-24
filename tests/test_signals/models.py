#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Copyright (c) Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can do what the LICENCE file allows you to.
#
from xoeuf import api, models, fields, signals
from lxml import etree


class FVG(models.AbstractModel):
    _name = "test_signals.fvg"

    @api.model
    def fields_view_get(
        self, view_id=None, view_type="form", toolbar=False, submenu=False
    ):
        result = super(FVG, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu
        )
        if view_type == "form":
            doc = etree.XML(result["arch"])
            for node in doc.xpath('//field[@name="name"]'):
                node.set("fgv-is-present", "yes")
            result["arch"] = etree.tostring(doc)
        return result


class SignalingModel(models.Model):
    _name = "test_signals.signaling_model"
    _inherit = ["test_signals.fvg"]

    name = fields.Char()


@signals.receiver(signals.post_save, sender="test_signals.signaling_model")
def post_save_receiver(sender, signal, **kwargs):
    pass


@signals.receiver(signals.post_save)
def post_save_receiver_all_models(sender, signal, **kwargs):
    pass


@signals.receiver(signals.pre_save, sender="test_signals.signaling_model")
def pre_save_receiver(sender, signal, **kwargs):
    pass


@signals.wrapper(signals.write_wrapper, sender="test_signals.signaling_model")
def wrap_nothing(sender, wrapping, *args, **kwargs):
    yield


@signals.receiver(signals.pre_search, sender="test_signals.signaling_model")
def pre_search_receiver(sender, signal, **kwargs):
    pass


@signals.receiver(signals.pre_fields_view_get, sender="test_signals.signaling_model")
def pre_fvg_receiver(sender, signal, **kwargs):
    pass
