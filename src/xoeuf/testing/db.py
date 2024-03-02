#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Copyright (c) Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can do what the LICENCE file allows you to.
#
import uuid
import decorator

__all__ = ["rollbacked"]


def rollbacked(fn):
    """A decorator that always rollbacks a SAVEPOINT.

    This can only be applied to methods of a TransactionCase.  It's useful to
    use in tests with hypothesis, like this::

        class TestCaseX(TransactionCase):
            @hypothesis.given(...)
            @rollbacked
            def test_something(self, ...):
                ...

    .. important:: You must put ``@rollback`` below the decorator
       ``@hypothesis.given``.

    """

    def test(fn, self, *args, **kwargs):
        name = next(savepoint_name)
        self.env.cr.execute(f'SAVEPOINT "{name}"')
        try:
            return fn(self, *args, **kwargs)
        finally:
            self.env.cr.execute(f'ROLLBACK TO SAVEPOINT "{name}"')

    return impersonate(fn)(decorator.decorate(fn, test))


NS = uuid.uuid1().hex


def _names():
    count = 0
    while True:
        count += 1
        yield f"{NS}-{count}"


savepoint_name = _names()


# The following functions has been taken from the source code of hypothesis.


def update_code_location(code, newfile, newlineno):
    """Take a code object and lie shamelessly about where it comes from.

    Why do we want to do this? It's for really shallow reasons involving
    hiding the hypothesis_temporary_module code from test runners like
    pytest's verbose mode. This is a vastly disproportionate terrible
    hack that I've done purely for vanity, and if you're reading this
    code you're probably here because it's broken something and now
    you're angry at me. Sorry.
    """
    if hasattr(code, "replace"):
        # Python 3.8 added positional-only params (PEP 570), and thus changed
        # the layout of code objects.  In beta1, the `.replace()` method was
        # added to facilitate future-proof code.  See BPO-37032 for details.
        return code.replace(co_filename=newfile, co_firstlineno=newlineno)

    # This field order is accurate for 3.5 - 3.7, but not 3.8 when a new field
    # was added for positional-only arguments.  However it also added a .replace()
    # method that we use instead of field indices, so they're fine as-is.
    CODE_FIELD_ORDER = [
        "co_argcount",
        "co_kwonlyargcount",
        "co_nlocals",
        "co_stacksize",
        "co_flags",
        "co_code",
        "co_consts",
        "co_names",
        "co_varnames",
        "co_filename",
        "co_name",
        "co_firstlineno",
        "co_lnotab",
        "co_freevars",
        "co_cellvars",
    ]
    unpacked = [getattr(code, name) for name in CODE_FIELD_ORDER]
    unpacked[CODE_FIELD_ORDER.index("co_filename")] = newfile
    unpacked[CODE_FIELD_ORDER.index("co_firstlineno")] = newlineno
    return type(code)(*unpacked)


def impersonate(target):
    """Decorator to update the attributes of a function so that to external
    introspectors it will appear to be the target function.

    Note that this updates the function in place, it doesn't return a
    new one.
    """

    def accept(f):
        f.__code__ = update_code_location(
            f.__code__, target.__code__.co_filename, target.__code__.co_firstlineno
        )
        f.__name__ = target.__name__
        f.__module__ = target.__module__
        f.__doc__ = target.__doc__
        return f

    return accept
