#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Copyright (c) Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can do what the LICENCE file allows you to.
#
"""Xœuf basic ORM extensions for Open Object (OpenERP) models."""

from collections.abc import Mapping

from xotl.tools.deprecation import deprecated

from xoeuf.models import get_modelname as _get_modelname
from xoeuf.tools import add_symbols_to_xmls

get_modelname = deprecated("xoeuf.models.get_modelname")(_get_modelname)
del _get_modelname, deprecated


def guess_id(which, attr="id"):
    """Guess the id of an object.

    If `which` is an integer, it is returned unchanged.  If it is a dict
    or a browse_record the attribute/key given by `attr` is look up and
    return.  If not found an AttibuteError is raised.  Any other type is a
    TypeError.

    """
    from odoo.osv.orm import browse_record

    if isinstance(which, int):
        return which
    elif isinstance(which, (Mapping, browse_record)):
        from xotl.tools.objects import smart_getter

        get = smart_getter(which, strict=True)
        return get(attr)
    else:
        raise TypeError("Object %r of invalid type" % which)


def store_identity(self, cr, uid, ids, context=None):
    """To be used in ``store`` parameter for functional fields when monitor
    is needed for fields in a local model.

    For example::

        'active':
            fields.function(_get_active, type='boolean', string='Active?',
                store={_name: (store_identity, ['contract_ids'], 10), }),

    """
    return ids


# Making this a subclass of int allows to be reliably tested for equality in
# both Python 2.7 and Python 3.4
class _Command(int):
    def __new__(cls, value, *args):
        return super(_Command, cls).__new__(cls, value)

    def __init__(self, value, _lambda):
        self.value = value
        self._lambda = _lambda

    def __call__(self, *args, **kwargs):
        if callable(self._lambda):
            return self._lambda(*args, **kwargs)
        else:
            return self._lambda


# The index where the command magic number is in tuples
COMMAND_INDEX = 0

# For applicable commands this is the index where id/ids are located.
ID_INDEX = 1

# For applicable commands this is the index where values are located
VALUE_INDEX = VALUES_INDEX = -1


#: Returns a single "command" to create a new related record
CREATE_RELATED = _Command(0, lambda **values: (0, 0, values))
ONE2MANY_CREATE = MANY2MANY_CREATE = CREATE_RELATED

#: Returns a single "command" to update a linked record
UPDATE_RELATED = _Command(1, lambda id, **values: (1, id, values))
ONE2MANY_UPDATE = MANY2MANY_UPDATE = UPDATE_RELATED

#: Returns a single "command" to remove (and unlink) the related record
REMOVE_RELATED = _Command(2, lambda id: (2, id))
ONE2MANY_REMOVE = MANY2MANY_REMOVE = REMOVE_RELATED

#: Returns a single command to forget about a relation
FORGET_RELATED = _Command(3, lambda id: (3, id))

#: Returns a single command to link a record
LINK_RELATED = _Command(4, lambda id: (4, id))

#: Returns a single command to unlink all
UNLINKALL_RELATED = _Command(5, lambda: (5,))

#: Returns a single command to replace all related with existing ids
REPLACEWITH_RELATED = _Command(6, lambda *ids: (6, 0, list(ids)))


add_symbols_to_xmls(
    CREATE_RELATED=CREATE_RELATED,
    UPDATE_RELATED=UPDATE_RELATED,
    REMOVE_RELATED=REMOVE_RELATED,
    FORGET_RELATED=FORGET_RELATED,
    LINK_RELATED=LINK_RELATED,
    UNLINKALL_RELATED=UNLINKALL_RELATED,
    REPLACEWITH_RELATED=REPLACEWITH_RELATED,
)
