#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Copyright (c) Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can do what the LICENCE file allows you to.
#
from odoo.fields import Html as Base

from lxml import html
from lxml.etree import XMLSyntaxError

from xoeuf.utils import hybridmethod


class Html(Base):
    """An HTML field.

    This is an extension to Odoo's fields.Html to add a couple of methods.

    """

    @hybridmethod
    def extract_text(self_or_cls, record_or_value, raises=True):
        """Extract plain text from an HTML field.

        If given value cannot be parsed and `raises` is True, raise a
        ValueError; if `raises` is False return None.

        This method can be called as classmethod, or as instance method.  In
        the first case, the argument should a string with the contents of the
        HTML.  In the second case, the argument should be a singleton
        recordset from which we extract the field's value.

        .. versionadded:: 0.74.0

        """
        value = self_or_cls._get_html_value(record_or_value)
        if value:
            try:
                texts = html.fromstring(value).xpath("//text()")
            except XMLSyntaxError:
                if raises:
                    raise
                else:
                    return None
            else:
                if texts:
                    return " ".join(texts)
        return ""

    @hybridmethod
    def is_plain_text_empty(self_or_cls, record_or_value, raises=True):
        """Return True if the plain text of HTML value is empty.

        If `raises` is False and the value is not valid (i.e
        `Html.extract_text`:method: returns None), return None.  If `raises`
        is True, raise a ValueError.

        This method can be called as classmethod, or as instance method.  In
        the first case, the argument should a string with the contents of the
        HTML.  In the second case, the argument should be a singleton
        recordset from which we extract the field's value.

        .. versionadded:: 0.74.0

        """
        res = self_or_cls.extract_text(record_or_value, raises=raises)
        if res is not None:
            return not res.strip()
        else:
            return None

    @hybridmethod
    def _get_html_value(self_or_cls, record_or_value):
        if isinstance(self_or_cls, type) and issubclass(self_or_cls, Base):
            return record_or_value
        else:
            return record_or_value[self_or_cls.name]
