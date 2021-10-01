#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Copyright (c) Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can do what the LICENCE file allows you to.
#

"""Secures a DB by:

- Changing all passwords

- [TODO] Changing all accounting related data by a random mapping.

"""
from collections import abc
from . import Command


class Secure(Command):
    """The secure command."""

    @classmethod
    def get_arg_parser(cls):
        from xotl.tools.crypto import PASS_LEVEL_NAME_MAPPING
        from xotl.tools.crypto import DEFAULT_PASS_PHRASE_LEVEL

        def path(extensions=None):
            """A type-builder for file arguments."""
            from os.path import abspath, isfile, splitext

            if extensions and not is_collection(extensions):
                extensions = (extensions,)
            acceptable = lambda ext: not extensions or ext in extensions

            def inner(value):
                res = abspath(value)
                name, extension = splitext(value)
                if not isfile(res) or not acceptable(extension):
                    raise TypeError("Invalid filename %r" % res)
                return res

            return inner

        res = getattr(cls, "_arg_parser", None)
        if not res:
            from argparse import ArgumentParser

            res = ArgumentParser()
            cls._arg_parser = res
            res.add_argument(
                "-c",
                "--config",
                dest="conf",
                required=False,
                default=None,
                type=path(),
                help="A configuration file.  This could be "
                "either a Python file, like that required by "
                "Gunicorn deployments, or a INI-like "
                'like the standard ".openerp-serverrc".',
            )
            res.add_argument(
                "-l",
                "--level",
                dest="security_level",
                choices=PASS_LEVEL_NAME_MAPPING.keys(),
                default=DEFAULT_PASS_PHRASE_LEVEL,
                help="The security level for passwords.  If "
                '"basic" the password will the same as the '
                'user\'s login.  "random" means a truly random '
                "password.",
            )
            res.add_argument(
                "-d",
                "--database",
                dest="database",
                type=cls.database_factory,
                required=True,
            )
            loggroup = res.add_argument_group("Logging")
            loggroup.add_argument(
                "--log-level",
                choices=("debug", "warning", "info", "error"),
                default="warning",
                help="How much to log",
            )
        return res

    @classmethod
    def database_factory(cls, database):
        from odoo import api, SUPERUSER_ID
        from odoo.modules.registry import Registry

        db = Registry(database)
        env = api.Environment(db.cursor(), SUPERUSER_ID, {})
        return env["res.users"]

    def run(self, args=None):
        from xoeuf.security import reset_all_passwords

        parser = self.get_arg_parser()
        options = parser.parse_args(args)
        conffile = options.conf
        level = options.security_level
        if conffile:
            self.read_conffile(conffile)
        self = options.database
        with self.env.cr:
            reset_all_passwords(self, security_level=level)

    def read_conffile(self, filename):
        import os

        ext = os.path.splitext(filename)[-1]
        if ext == ".py":
            self.load_config_from_script(filename)
        else:
            self.load_config_from_inifile(filename)

    @staticmethod
    def load_config_from_script(filename):
        cfg = {
            "__builtins__": __builtins__,
            "__name__": "__config__",
            "__file__": filename,
            "__doc__": None,
            "__package__": None,
        }
        try:
            with open(filename, "rb") as fh:
                return exec(compile(fh.read(), filename, "exec"), cfg, cfg)
        except Exception:
            import traceback
            import sys

            print("Failed to read config file: %s" % filename)
            traceback.print_exc()
            sys.exit(1)

    @staticmethod
    def load_config_from_inifile(filename):
        from odoo.tools import config

        config.rcfile = filename
        config.load()


def is_collection(which):
    return isinstance(which, abc.Collection) and not isinstance(which, (str, bytes))
