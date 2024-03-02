#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Copyright (c) Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can do what the LICENCE file allows you to.
#

"""Profiling tools.

For development only purposes.

"""

from xotl.tools.decorator.meta import decorator

try:
    from line_profiler import LineProfiler

    profiler = LineProfiler()

    @decorator
    def profile(func, model=True, stream=None):
        """Decorate `func` to activate the line profiler.

        :param func: The function to decorate

        :param model: Set to False if this function is not contained in an
                      Odoo model class definition.

        :param stream:  The stream into which print the collected stats.  The
                        default is whatever LineProfiler has as default.

        """
        from xoeuf import api

        if model:
            f = getattr(func, "_orig", func)
            wraps = api.mimic
        else:
            f = func
            wraps = lambda f: lambda x: x  # noqa

        profiler.add_function(f)

        @wraps(func)
        def inner(*args, **kwargs):
            profiler.enable_by_count()
            try:
                return f(*args, **kwargs)
            finally:
                profiler.disable_by_count()
                profiler.print_stats(stream)

        return inner

except ImportError:
    import warnings

    profiler = None

    @decorator
    def profile(func, model=None, stream=None):
        """Decorate `func` to activate the line profiler."""
        warnings.warn(
            "Trying to the profiler without the line_profiler package.  "
            "Are you trying to use the profiler in production?! "
            "Don't do that EVER AGAIN!!",
            stacklevel=1,
        )
        return func


del decorator
