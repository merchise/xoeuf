#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Copyright (c) Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can do what the LICENCE file allows you to.
#

"""Xœuf services for access Open Object (OpenERP) models.

Implement the network protocols that the Xœuf applications that access OpenERP
databases uses to communicate with its clients.

"""

import pytz

from xoeuf.tools import dt_as_timezone


def savepoint(cr, name=None):
    """A context manager that enters a new savepoint.

    If `name` is not provided a random one is generated.

    .. note:: In Odoo v8, the cursor `cr` has already a ``savepoint`` method.
              This function will fallback to it in this case.  However, the
              argument `name` will be ignored in this case.

    """
    from xotl.tools.symbols import Unset

    _savepoint = getattr(cr, "savepoint", Unset)
    if _savepoint is Unset:
        from contextlib import contextmanager

        if not name:
            from xotl.tools.uuid import uuid

            name = uuid(True)

        @contextmanager
        def _savepoint():
            cr.execute('SAVEPOINT "%s"' % name)
            try:
                yield
            except:  # noqa
                cr.execute('ROLLBACK TO SAVEPOINT "%s"' % name)
                raise
            else:
                cr.execute('RELEASE SAVEPOINT "%s"' % name)

    return _savepoint()


def datetime_user_to_server_tz(cr, uid, userdate, tz_name=None, context=None):
    """Convert date values expressed in user's timezone to
    server-side UTC timestamp.

    :param datetime userdate: datetime in user time zone
    :return: UTC datetime for server-side use
    """
    from xoeuf import api

    utc = pytz.UTC
    if userdate.tzinfo:
        return utc.normalize(userdate)
    if not tz_name:
        env = api.Environment(cr, uid, context or {})
        user = env.user
        if user.tz:
            dt = dt_as_timezone(userdate, user.tz)
        else:
            dt = dt_as_timezone(userdate)
    else:
        dt = dt_as_timezone(userdate, tz_name)
    return utc.normalize(dt)


def datetime_server_to_user_tz(cr, uid, serverdate, tz_name=None, context=None):
    """Convert date values expressed in server-side UTC timestamp to
    user's timezone.

    :param datetime serverdate: datetime in server-side UTC timestamp.
    :return: datetime on user's timezone
    """
    from xoeuf import api

    dt = dt_as_timezone(serverdate)  # datetime in UTC
    if not tz_name:
        env = api.Environment(cr, uid, context or {})
        user = env.user
        user_tz = pytz.timezone(user.tz) if user.tz else pytz.UTC
    else:
        user_tz = pytz.timezone(tz_name)
    return user_tz.normalize(dt)
