#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Copyright (c) Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can do what the LICENCE file allows you to.
#
from odoo.fields import *  # noqa

from .datetime import LocalizedDatetime  # noqa
from .properties import Property  # noqa
from .monetary import Monetary  # noqa
from .timespan import TimeSpan  # noqa
from .enumeration import Enumeration  # noqa
from .timezone import TimezoneSelection  # noqa
from .timedelta import TimeDelta  # noqa
from .one2one import One2one  # noqa
from .timerange import TimeRange  # noqa
from .reference import TypedReference  # noqa
from .html import Html  # noqa


try:
    del Serialized  # noqa
except NameError:
    pass
