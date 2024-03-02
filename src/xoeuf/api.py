#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Copyright (c) Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can do what the LICENCE file allows you to.
#
"""Odoo API Extensons."""

from odoo import api as _odoo_api
from xotl.tools.decorator.meta import decorator as _xdecorator

# TODO: `copy_members` is deprecated since xotl.tools 1.8, use instead the same
# mechanisms as `xotl.tools.future`.
from xotl.tools.modules import copy_members as _copy_python_module_members

this = _copy_python_module_members(_odoo_api)
del _copy_python_module_members


def contextual(func):
    """Decorate a function to run within a proper Odoo environment.

    You should decorate every function that represents an "entry point" for
    working with the ORM.  A proper `Environment`:class: is entered upon
    calling the function.

    """

    def inner(*args, **kwargs):
        with _odoo_api.Environment.manage():
            return func(*args, **kwargs)

    return inner


def requires_singleton(f):
    """An idiomatic alias for `api.multi()`.

    This is exactly the same as `api.multi()`, however it's expected to be
    used when the code you're decorating requires a singleton recordset.

    Notice we don't fail at the method call, but only if the actual code
    executes a command that requires such a condition to be met (for instance,
    accessing a field in ``self``.)

    """
    return _odoo_api.multi(f)


def mimic(original):
    """Apply the API guess of `original` to the decorated function.

    Usage::

       def f1(self, cr, uid, ids, context=None):
           # Actually any valid signature

       @api.mimic(f1)
       def f2(*args, **kwargs):
           pass

    """
    import types

    method = _odoo_api.guess(original)
    # Odoo stores the decorator in the _api attribute.  But Odoo 10 only
    # stores the name of the API method.
    decorator = method._api
    if isinstance(decorator, types.FunctionType):
        return decorator
    else:
        return getattr(_odoo_api, decorator)


@_xdecorator
def from_active_ids(f, leak_context=False):
    """Decorator that ensures `self` comes from 'active_ids' in the context.

    The context key 'active_model' must be set and match the recordset's
    model.  If the 'active_model' key does not match the recordset's model,
    call `f` with the given recordset, i.e act like `api.multi`:func:.

    If 'active_model' matches the recordset's, and 'active_ids' is not empty,
    run `f` with the recordset of active ids.

    `f` is automatically decorated with `api.multi`:func:.

    The expected use is in methods from a server action linked to an
    ir.value.  In those cases `self` is normally the first selected record,
    but you want it to be run with all selected records.

    If `leak_context` is False (the default), calls to other methods decorated
    with `from_active_ids`:func: won't take the ids from the 'active_ids'.

    .. versionchanged:: 0.34.0 Add the `leak_context` argument.  And allow `f`
       to take arguments (other than `self`).

    .. versionchanged:: 0.35.0 The `leak_context` defaults to False, and it
       does not change the 'active_model' key in the context.

    """
    from functools import wraps

    from xotl.tools.context import Context

    @multi  # noqa
    @wraps(f)
    def inner(self, *args, **kwargs):
        model = self._name
        if _SKIP_ACTIVE_IDS in Context:
            this = self
        else:
            active_model = self.env.context.get("active_model")
            if active_model == model:
                active_ids = self.env.context.get("active_ids", ())
                if active_ids:
                    this = self.browse(active_ids)
                else:
                    this = self
            else:
                this = self
        with leaking_context(leak_context):
            return f(this, *args, **kwargs)

    return inner


_SKIP_ACTIVE_IDS = object()
_DONT_SKIP_ACTIVE_IDS = object()


def leaking_context(leak=False):
    from xotl.tools.context import Context

    if not leak:
        return Context(_SKIP_ACTIVE_IDS)
    else:
        return Context(_DONT_SKIP_ACTIVE_IDS)


def onupdate(*args):
    """A decorator to trigger updates on dependencies.

    Return a decorator that specifies the field dependencies of an updater
    method.  Each argument must be a string that consists in a dot-separated
    sequence of field names::

        @api.onupdate('partner_id.name', 'partner_id.is_company')
        def update_pname(self):
            for record in self:
                if record.partner_id.is_company:
                    record.pname = (record.partner_id.name or "").upper()
                else:
                    record.pname = record.partner_id.name

    One may also pass a single function as argument. In that case, the
    dependencies are given by calling the function with the field's model.

    .. note:: ``@onupdate`` is very similar to ``@constraint`` but with just
       one key difference: It allow dot-separated fields in arguments.

    .. versionadded: 0.46.0

    """
    if args and callable(args[0]):
        args = args[0]
    elif any("id" in arg.split(".") for arg in args):
        raise NotImplementedError("Updater method cannot depend on field 'id'.")
    return _odoo_api.attrsetter("_onupdates", args)
