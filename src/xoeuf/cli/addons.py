#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Copyright (c) Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can do what the LICENCE file allows you to.
#
from . import Command


class Addons(Command):
    """List all non-uninstallable addons found in the DB."""

    @classmethod
    def get_arg_parser(cls):
        res = getattr(cls, "_arg_parser", None)
        if not res:
            from argparse import ArgumentParser

            res = ArgumentParser()
            cls._arg_parser = res
            res.add_argument("-f", "--filter", dest="filters", default=[], action="append")
        return res

    @classmethod
    def database_factory(cls, database):
        import importlib

        module = "xoeuf.pool.%s" % database
        return importlib.import_module(module)

    def run(self, args=None):
        parser = self.get_arg_parser()
        options = parser.parse_args(args)
        filters = options.filters
        self.list_addons(filters)

    def list_addons(self, filters):
        addons = self.get_addons(filters)
        for addon in addons:
            print(addon)

    def get_addons(self, filters):
        from odoo.modules import get_modules

        return [
            addon
            for addon in get_modules()
            if not filters or any(addon.startswith(f) for f in filters)
        ]
