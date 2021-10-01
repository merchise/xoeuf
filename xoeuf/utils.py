#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Copyright (c) Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can do what the LICENCE file allows you to.
#
try:
    from xotl.tools.objects import crossmethod  # TODO: migrate
except ImportError:

    class crossmethod(object):
        """Decorate a function as static or instance level.

        Example:

          >>> class Mule(object):
          ...     @crossmethod
          ...     def print_args(*args):
          ...         print(args)

          # Call it as a staticmethod
          >>> Mule.print_args()
          ()

          # Call it as an instance
          >>> Mule().print_args()   # doctest: +ELLIPSIS
          (<...Mule object at ...>,)

        .. note:: This is different from `hybridmethod`:func:.  Hybrid method
                  always receive the implicit argument (either `cls` or
                  `self`).

        """

        def __init__(self, func):
            self.func = func

        def __get__(self, instance, owner):
            if instance is None:
                return self.func
            else:
                return self.func.__get__(instance, owner)


try:
    from xotl.tools.objects import hybridmethod  # TODO: migrate
except ImportError:
    # Code taken from SQLAlchemy
    #
    # Copyright (C) 2005-2016 the SQLAlchemy authors and contributors
    #
    # SQLAlchem is released under the MIT License:
    # http://www.opensource.org/licenses/mit-license.php

    class hybridmethod:
        """Decorate a function as cls- or instance- level."""

        def __init__(self, func):
            self.func = func
            self.__func__ = func

        def __get__(self, instance, owner):
            if instance is None:
                return self.func.__get__(owner, owner.__class__)
            else:
                return self.func.__get__(instance, owner)
