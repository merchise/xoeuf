#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Copyright (c) Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can do what the LICENCE file allows you to.
#
"""Xœuf are basic services for OpenERP and Open Object.

The name is composed by:
  * x: The starting letter for almost all Merchise projects.
  * oe: Open and ERP initials.
  * œuf: Is "egg" in french.

"""

from . import models  # bootstrap 'xoeuf.odoo'
from . import signals
from .osv import orm  # bootstrap 'orm' (injects _RELATED in XMLs 'eval')

from odoo import SUPERUSER_ID
from odoo.release import version_info as ODOO_VERSION_INFO

# Bootstrap fields; otherwise they won't appear in the FIELD_TYPES in
# ir_model.py
from . import fields

MAJOR_ODOO_VERSION = ODOO_VERSION_INFO[0]

try:
    from ._version import version as __version__
except ImportError:
    __version__ = "dev"

del orm

__all__ = (
    "models",
    "signals",
    "fields",
    "SUPERUSER_ID",
    "ODOO_VERSION_INFO",
    "MAJOR_ODOO_VERSION",
)
