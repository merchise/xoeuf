#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Copyright (c) Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can do what the LICENCE file allows you to.
#
from xotl.tools.future.datetime import TimeSpan, parse_date

from datetime import date
from hypothesis import strategies, given

from odoo.tests.common import TransactionCase

from xoeuf.testing.db import rollbacked


maybe_dates = strategies.dates(min_value=date(1900, 1, 1)) | strategies.none()


@strategies.composite
def timespans(draw):
    start = draw(maybe_dates)
    end = draw(maybe_dates)
    return TimeSpan(start, end)


class TestTimespan(TransactionCase):
    def setUp(self):
        super(TestTimespan, self).setUp()
        self.Value = self.env["test.timespan.value"]

    def assertDateEqual(self, value1, value2):
        if value1 and value2:
            if isinstance(value1, date):
                v1 = value1
                # Ensure we're using date1 with the Python's date.  See
                # xotl.tools bug:
                # https://gitlab.lahavane.com/merchise/xoutil/issues/3
                date1 = date(value1.year, value1.month, value1.day)
            else:
                v1 = parse_date(value1)
                date1 = value1
            if isinstance(value2, date):
                v2 = value2
                date2 = date(value2.year, value2.month, value2.day)
            else:
                v2 = parse_date(value2)
                date2 = value2
            self.assertTrue(v1 == v2, "%r is not equal to %r" % (date1, date2))
        else:
            return value1 in (False, None) and value2 in (False, None)

    @given(timespans())
    @rollbacked
    def test_create(self, value):
        obj = self.Value.create({"period": value})
        self.assertDateEqual(obj.start_date, value.start_date)
        self.assertDateEqual(obj.end_date, value.end_date)

    @given(maybe_dates, maybe_dates)
    @rollbacked
    def test_create2(self, start, end):
        obj = self.Value.create({"start_date": start, "end_date": end})
        self.assertEqual(obj.period, TimeSpan(start, end))

    @given(timespans())
    @rollbacked
    def test_set(self, value):
        obj = self.Value.create({})
        obj.period = value
        self.assertDateEqual(obj.start_date, value.start_date)
        self.assertDateEqual(obj.end_date, value.end_date)

    @given(maybe_dates, maybe_dates)
    @rollbacked
    def test_set2(self, start, end):
        obj = self.Value.create({})
        obj.start_date = start
        obj.end_date = end
        self.assertEqual(obj.period, TimeSpan(start, end))
