#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Copyright (c) Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can do what the LICENCE file allows you to.
#

"""An example of an application that use :mod:`xoeuf.cli`.

It behaves similar to "openerp-server" script. This module does not provide any
external facilities, but uses :func:`xotl.tools.cli.app.main` to run the
OpenERP server. Usage::

  $ python server.py [options...]

"""


def server():
    from xoeuf.cli import DEFAULT_COMMAND
    from xotl.tools.cli.app import main

    main(default=DEFAULT_COMMAND)


if __name__ == "__main__":
    server()
