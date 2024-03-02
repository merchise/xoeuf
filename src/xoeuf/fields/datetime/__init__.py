#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Copyright (c) Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can do what the LICENCE file allows you to.
#
import pytz
from odoo import fields

from ...tools import localtime_as_remotetime


class LocalizedDatetime(fields.Datetime):
    """A field for localized datetimes.

    Localized datetimes are actually a functional field that takes two
    underlying columns a datetime and timezone name.

    :param dt: The name of the column where the datetime (in UTC) is actually
               saved.

    :param tzone:  The name of the column where the timezone where the event
                   should be presented to the user.

    Upon reading, we assume the user's timezone is properly set.

    The datetime column will be actually saved in UTC as all datetimes in
    Odoo.  But upon reading we convert to a properly shifted datetime so that
    is presented to the user in the saved time zone.

    .. note:: At the time this field is not searchable, and non-storable.

    """

    _slots = {"dt_field": "", "tzone_field": "", "store": False}

    def __init__(self, dt_field=None, tzone_field=None, **kwargs):
        # Include store=False if is not include in kwargs
        if not dt_field or not tzone_field:
            raise TypeError("LocalizedDatetime requires the surrogates fields")
        self.dt_field = dt_field
        self.tzone_field = tzone_field
        kwargs = dict(
            {"store": False, "copy": False, "dt_field": dt_field, "tzone_field": tzone_field},
            **kwargs,
        )
        super().__init__(**kwargs)

    def new(self, **kwargs):
        # Pass original args to the new one.  This ensures that the
        # tzone_field and dt_field are present.  In odoo/models.py, Odoo calls
        # this `new()` without arguments to duplicate the fields from parent
        # classes.
        kwargs = dict(self.args, **kwargs)
        return super().new(**kwargs)

    def _setup_regular_full(self, model):
        # This is to support the case where ModelB `_inherits` from a ModelA
        # with a localized datetime.  In such a case, we don't override the
        # compute method.
        super()._setup_regular_full(model)
        self.depends = tuple(f for f in (self.dt_field, self.tzone_field) if f)
        self.compute = self._compute
        if not self.readonly:
            self.inverse = self._inverse
        self.search = self._search

    def _compute(self, records):
        tzone_field = self.tzone_field
        dt_field = self.dt_field
        tz = records._context.get("tz", None)
        if not tz:
            user = records.env.user
            tz = pytz.timezone(user.tz) if user.tz else pytz.UTC
        else:
            tz = pytz.timezone(tz)
        for item in records:
            tzone = getattr(item, tzone_field)
            if not tzone:
                tzone = pytz.UTC
            else:
                tzone = pytz.timezone(tzone)
            dt = getattr(item, dt_field)
            # Compute the datetime in users timezone,
            # then force to it the desired TZ and back to UTC.
            if dt and tz != tzone:
                dt = localtime_as_remotetime(dt, tzone, tz)
            setattr(item, self.name, dt)

    def _inverse(self, records):
        tzone_field = self.tzone_field
        dt_field = self.dt_field
        tz = records._context.get("tz", None)
        if not tz:
            user = records.env.user
            tz = pytz.timezone(user.tz) if user.tz else pytz.UTC
        else:
            tz = pytz.timezone(tz)
        for item in records:
            tzone = getattr(item, tzone_field)
            if not tzone:
                tzone = pytz.UTC
            else:
                tzone = pytz.timezone(tzone)
            dt = getattr(item, self.name)
            # Compute the datetime in the desired timezone, then
            # extract all datetime components but the TZ and localize
            # it to the users TZ and convert it back to UTC...
            # This makes the UI to reverse the process and show the
            # datetime in the desired timezone.
            if dt and tz != tzone:
                dt = localtime_as_remotetime(dt, tz, tzone)
            setattr(item, dt_field, dt)

    def _search(self, records, operator, value):
        # TODO: localize value.
        return [(self.dt_field, operator, value)]
