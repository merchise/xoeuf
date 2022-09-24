#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------
# Copyright (c) Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can do what the LICENCE file allows you to.
#
from xoeuf import fields, models

TIME_RANGE_SELECTION = [
    ("morning", "Morning", "6:00", "11:59"),
    ("noon", "Noon", "12:00", "13:59"),
    ("afternoon", "Afternoon", "14:00", "18:59"),
]


class TestTimeRange(models.Model):
    _name = "test.time.range"

    time_value = fields.Float()
    range_value = fields.TimeRange(
        time_field="time_value", selection=TIME_RANGE_SELECTION
    )
    tz = fields.Char()
    datetime_value = fields.Datetime(default=lambda self: fields.Datetime.today())
    range_datetime = fields.TimeRange(
        time_field="datetime_value", tzone_field="tz", selection=TIME_RANGE_SELECTION
    )
