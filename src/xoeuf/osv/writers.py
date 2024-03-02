#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Copyright (c) Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can do what the LICENCE file allows you to.
#
"""Helpers to generate ``BaseModel.write`` commands."""

from collections.abc import Collection

from odoo import fields


class _BaseWriter(object):
    """Core of the function for `ORMWriter`:class: and `ORMCreator`:class:.

    .. warning:: Currently we don't support nested context managers.

    """

    def __init__(self, model):
        from xotl.tools.future.collections import StackedDict

        self.model = model
        self._commands = StackedDict()
        self.result = None

    def _get_field(self, attrname):
        return self.model._fields[attrname]

    __getitem__ = _get_field

    def _is_many2many(self, attrname):
        return isinstance(self[attrname], fields.Many2many)

    def _is_one2many(self, attrname):
        return isinstance(self[attrname], fields.One2many)

    @property
    def commands(self):
        """The current stack of commands at the current level.

        Since commands could be nested, this will only return the
        top-of-the-stack commands.

        :rtype: dict

        """
        # TODO: Deal with nested writers properly.
        return self._commands.peek()

    def __enter__(self):
        self._commands.push_level()
        return self

    def __exit__(self, ex_type, exc_value, exc_tb):
        raise NotImplementedError

    def create(self, attrname, **values):
        """Issues a command to create a newly related object with given `values` for
        the many2many/one2many column `attrname`.

        """
        assert self._is_many2many(attrname) or self._is_one2many(attrname)
        from .orm import CREATE_RELATED

        cmds = self._commands.setdefault(attrname, [])
        cmds.append(CREATE_RELATED(**values))

    def update(self, *replacement, **values):
        """Issues update commands.

        There are two possible signatures for this method:

        - Keywords only `attrname=value`.  This case is used mostly for
          "plain" columns.  If any `attrname` is a relation it must be a
          many2many, and value must be either None or a list of all related
          objects' ids.

        - Two positional arguments and several keyword arguments, like
          ``update(attrname, id, **values)``.  This is for updating the
          attributes of a single related object.  In this case `attrname` must
          be either a many2many or one2many column.

        """
        from .orm import UPDATE_RELATED

        commands = self._commands
        if replacement:
            attrname, id = replacement
            assert self._is_many2many(attrname) or self._is_one2many(attrname)
            cmds = commands.setdefault(attrname, [])
            cmds.append(UPDATE_RELATED(id, **values))
        else:
            for attrname, val in values.items():
                if self._is_many2many(attrname):
                    if val is None:
                        self.forgetall(attrname)
                    elif isinstance(val, Collection):
                        self.replace(attrname, *tuple(val))
                    else:
                        raise TypeError(
                            "Malformed value '%s' for " "attribute %s" % (val, attrname)
                        )
                elif self._is_one2many(attrname):
                    raise TypeError("'update' does not allow one2many keyword" "arguments.")
                else:
                    commands[attrname] = val

    def remove(self, attrname, *ids):
        """Issues several "remove related object" commands for the attribute
        named `attrname`.

        """
        assert self._is_many2many(attrname) or self._is_one2many(attrname)
        from .orm import REMOVE_RELATED

        cmds = self._commands.setdefault(attrname, [])
        cmds.extend(REMOVE_RELATED(id) for id in ids)

    def forget(self, attrname, *ids):
        """Issues several "forget related object" commands for the attribute
        named `attrname`.

        """
        assert self._is_many2many(attrname)
        from .orm import FORGET_RELATED

        cmds = self._commands.setdefault(attrname, [])
        cmds.extend(FORGET_RELATED(id) for id in ids)

    def forgetall(self, attrname):
        """Issues a "forget all related objects" command for the attribute
        named `attrname`.

        """
        assert self._is_many2many(attrname)
        from .orm import UNLINKALL_RELATED

        cmds = self._commands.setdefault(attrname, [])
        cmds.append(UNLINKALL_RELATED())

    def replace(self, attrname, *ids):
        """Issues a "replace related objects" command for the attribute named
        `attrname`.

        """
        assert self._is_many2many(attrname)
        from .orm import REPLACEWITH_RELATED

        cmds = self._commands.setdefault(attrname, [])
        cmds.append(REPLACEWITH_RELATED(*ids))

    def add(self, attrname, *ids):
        """Issues several "link to" commands to the attribute named
        `attrname`.

        """
        from .orm import LINK_RELATED

        assert self._is_many2many(attrname)
        cmds = self._commands.setdefault(attrname, [])
        cmds.extend(LINK_RELATED(id) for id in ids)


class ORMWriter(_BaseWriter):
    """A context manager that eases writing objects with the Odoo's ORM.

    Two possible signatures:

    - ``get_writer(ModelRecordSet)``
    - ``get_writer(obj, cr, uid, ids, *, context=None)``

    .. warning:: `context` is a keyword-only argument.

    In the first case, ``ModelRecordSet`` should be a record set obtained from
    new API ``browse`` method. If the record set is empty, raise a ValueError.

    The second case is for the old API.

    Usage::

       with get_writer(obj, cr, uid, ids, context=context) as writer:
          writer.update(attr1=val1, attr2=val2, attr3=None)
          writer.update(attr4=val4)
          writer.add(many2manycolumn, id1, id2, id3)
          writer.forget(many2manycolumn, id4, id5)

    At the end of the `with` sentence the equivalent ``obj.write()`` method
    will be called.

    .. warning:: Non-magical disclaimer.

       The sole purpose of writers is to ease the writing of write sentences.
       If the OpenERP does not understand the commands you produce is not our
       fault.

    """

    def __init__(self, *args, **kwargs):
        try:
            if kwargs or len(args) > 1:
                context = kwargs.pop("context", None)
                _self, cr, uid, ids = args
                recordset = _self.browse(cr, uid, ids, context=context)
            elif len(args) == 1:
                recordset = args[0]
                if not recordset.ids:
                    raise ValueError("Invalid record set for get_writer")
            else:
                raise TypeError("Invalid signature for get_writer")
        except (KeyError, ValueError):
            raise TypeError("Invalid signature for get_writer") from None
        super().__init__(recordset)

    def __exit__(self, exc_type, exc_value, exc_tb):
        if exc_type or exc_value:
            return False
        # Both the new API and old API return True/False, no downgrade needed.
        self.result = self.model.write(self.commands)


class ORMCreator(_BaseWriter):
    """A context manager that eases creation of objects with Odoo's ORM.

    Two possible signatures:

    - ``get_creator(ModelRecordSet)``
    - ``get_creator(obj, cr, uid, ids, *, context=None)``

    .. warning:: `context` is a keyword-only argument.

    In the first case, ``ModelRecordSet`` should be a record set obtained from
    new API ``browse`` method.  The recordset may be empty.

    The second case is for the old API (we do the browse).

    This is similar to `get_writer`:func: but issues a 'create' call at the
    exit of the ``with`` block.  The context manager yields a creator that,
    after creating the object, stores the result in the attribute ``result``.
    If you use the new API call style, the ``result`` will be the record
    created.  If you use the old API call style, you'll get the id of created
    record.

    """

    def __init__(self, *args, **kwargs):
        try:
            if kwargs or len(args) > 1:
                context = kwargs.pop("context", None)
                _self, cr, uid = args
                self.downgrade = True
                model = _self.browse(cr, uid, [], context=context)
            elif len(args) == 1:
                self.downgrade = False
                model = args[0]
            else:
                raise TypeError("Invalid signature for get_creator")
        except (KeyError, ValueError):
            raise TypeError("Invalid signature for get_creator") from None
        super().__init__(model)

    def __exit__(self, exc_type, exc_value, exc_tb):
        if exc_type or exc_value:
            return False
        result = self.model.create(self.commands)
        if self.downgrade:
            # old API used, old API expectations returned
            self.result = result.id
        else:
            self.result = result

    set = _BaseWriter.update
