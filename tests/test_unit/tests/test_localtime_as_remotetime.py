#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Copyright (c) Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can do what the LICENCE file allows you to.
#
import unittest
import datetime
import pytz

from hypothesis import strategies, given, example
from hypothesis.extra.pytz import timezones
from xoeuf.tools import localtime_as_remotetime, normalize_datetime

from odoo.tests.common import BaseCase


class TestLocalAsRemote(BaseCase):
    @unittest.skip("Known failure")
    @given(
        strategies.datetimes(
            min_value=normalize_datetime("1912-04-14"),
            max_value=normalize_datetime("2100-12-31"),
        ),
        timezones(),
        timezones(),
    )
    @example(
        _dt=datetime.datetime(1946, 1, 1, 0, 0),
        from_tz=pytz.timezone("Europe/Kaliningrad"),
        to_tz=pytz.UTC,
    )
    def test_local_remote_time(self, _dt, from_tz, to_tz):
        _dt = normalize_datetime(_dt)
        self.assertEqual(
            _dt,
            localtime_as_remotetime(
                localtime_as_remotetime(_dt, from_tz, to_tz), to_tz, from_tz
            ),
        )
        self.assertEqual(
            _dt,
            localtime_as_remotetime(
                localtime_as_remotetime(_dt, from_tz, to_tz, ignore_dst=True),
                to_tz,
                from_tz,
                ignore_dst=True,
            ),
        )
