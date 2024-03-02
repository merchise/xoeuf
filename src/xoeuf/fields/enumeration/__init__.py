#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Copyright (c) Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can do what the LICENCE file allows you to.
#
import logging
from collections import Mapping, namedtuple

from odoo import api, fields, models
from odoo.fields import Char
from xotl.tools.objects import import_object
from xotl.tools.string import cut_prefix

logger = logging.getLogger(__name__)


__all__ = ["Enumeration"]

Member = namedtuple("Member", ("name", "value"))


class _EnumeratedField(object):
    # I'm keeping this class just in case someone has been testing for it.
    pass


class Enumeration(Char, _EnumeratedField):
    """Create an enumeration field.

    The `enumclass` argument must be either an `enumeration class` or a fully
    qualified name of an enumeration class.  If either way return a callable,
    it must accept a single argument (the model) and return the enumeration
    class.

    The actual enumeration used per model is stored in the ``Enumclass``
    attribute.

    The column in the DB will be of type CHAR and the values are the name of
    attribute in the enumeration class.

    Enumeration classes are required to:

    - have an attribute ``__members__`` with a `collections.Mapping`:class:
      from names to values.

    - have an attribute for each name in ``__member__`` with the same value as
      in the mapping.

    Those rules imply::

       >>> all(getattr(enumclass, name) is value
       ...     for name, value in enumclass.__members__.items())

    These requirements are compatible with Python 3.4's `enum.Enum`:class:
    However, we don't require that values are instances of the enumeration
    class.

    .. rubric:: Automatic selection field

    .. warning:: Known issues with this features.

       Up to 0.66.0 this feature is not yet stable.  The injected field is not
       visible to ``api.depends`` and other components of Odoo framework.

       However, the method `get_selection_field`:meth: seems to work well.

    Enumeration fields cannot be put in views because their values can be
    arbitrary Python objects which are not easily transferred to/from the web
    client.

    You can use the parameter 'selection_field_name' to automatically inject a
    computed Selection field that allows to represent this Enumeration in the
    web client.  This automatic is by default not stored in the DB.  Its
    values are the names of the members of the enumeration class.

    You may pass a function 'compute_member_string' which will be called to
    get the user facing text of each member.  The function will be passed both
    the name and value of the member.  By default we return the member's name.

    Additional keyword arguments starting with the prefix ``selection_field_``
    are used to construct the Selection field.  For instance,
    'selection_field_string' sets the argument 'string'.  If not provided, we
    set 'string', and 'help' to the same values of the Enumeration field.

    .. versionchanged:: 0.36.0 A new generalized enumeration field.  Maintains
       DB compatibility (does not need migrations), but do require changes in
       the code.

    .. versionchanged:: 0.47.0 Add keyword parameter 'force_char_column'.

    .. versionchanged:: 0.61.0 The DB column type is always a CHAR.  Ignore
       the parameter 'force_char_column'.

    .. versionchanged:: 0.61.0 Add an automatic way to create a selection
       field via the parameter 'selection_field_name'.

    .. versionchanged:: 0.64.0 The `enumclass` can be a callable.  Enumeration
       is now class instead of a function.  Gain the ``Enumclass`` attribute.

    .. versionchanged:: 0.66.0 The function `compute_member_string` must now
       take three arguments: the model, the name and the value.

    """

    type = "enumeration"

    _slots = {
        "enumclass": None,
        "selection_field_kwargs": None,
        "compute_member_string": None,
        "Enumclass": None,
    }

    def __init__(self, enumclass, *args, **kwargs):
        selection_field_kwargs = kwargs.pop("selection_field_kwargs", {})
        if not selection_field_kwargs:
            SELECTION_FIELD_PREFIX = "selection_field_"
            selection_field_kwargs = {
                cut_prefix(kw, SELECTION_FIELD_PREFIX): value
                for kw, value in kwargs.items()
                if kw.startswith(SELECTION_FIELD_PREFIX)
            }
            compute_member_string = kwargs.pop("compute_member_string", None)
            if compute_member_string:
                selection_field_kwargs["compute_member_string"] = compute_member_string

        super().__init__(
            *args,
            enumclass=enumclass,
            selection_field_kwargs=selection_field_kwargs,
            **kwargs,
        )
        self.enumclass = enumclass
        self.selection_field_kwargs = selection_field_kwargs

    def new(self, **kwargs):
        enumclass = kwargs.pop("enumclass", self.enumclass)
        selection_field_kwargs = kwargs.pop("selection_field_kwargs", self.selection_field_kwargs)
        return type(self)(
            enumclass=enumclass, selection_field_kwargs=selection_field_kwargs, **kwargs
        )

    def resolve_enumclass(self, model):
        enumclass = import_object(self.enumclass)

        if callable(enumclass) and not hasattr(enumclass, "__members__"):
            enumclass_factory = enumclass
        else:
            enumclass_factory = constant(enumclass)
        return enumclass_factory(model)

    def get_selection_field(
        self, field_name, selection_field_name, compute_member_string=None, **kwargs
    ):
        """Return a computed Selection field to set/get the Enumeration.

        The result is a standard `odoo.fields.Selection`:class: where the
        values are computed from the enumeration class.

        The argument to `compute_member_string`, if not None, should be a
        callable taking three arguments: the model, the name of a member, the
        value of a member; and it must return the display value of the
        selected member.

        The rest of the keyword arguments are passed to the selection
        unchanged.  We pass by default:

        compute
           Internal compute function that along with `inverse` below
           implements everything we've stated above.

        inverse
           Internal inverse function.

        store
           Set to False to avoid duplicating stuff in the DB -- the *real*
           value in the enumeration field.

        .. warning:: The first two arguments are annoying but required.

           The must be kept in sync with the enumeration field's name and the
           selection field's name.

        Comprehensive example:

        .. code-block:: python

           from enum import Enum
           from xoeuf import fields, models
           from odoo import _

           class Bark:
               __doc__ = _("Bark like a dog")

               @classmethod
               def make_sound(cls):
                   print("Woof!")

           class Meow:
               __doc__ = _("Meow like a cat")

               @classmethod
               def make_sound(cls):
                   print("Meow!")

           class enumclass(Enum):
               DOG = Bark
               CAT = Meow

           def get_cls_name(self, name, value):
              "Return the docstring as the name in the selection"
              doc = getattr(value, "__doc__", None)
              if doc:
                 return _(doc)
              else:
                 return name

           class Model(models.Model):
                animal = fields.Enumeration(enumclass)
                animal_sound = enum.get_selection_field(
                    "animal",
                    "animal_sound",
                    get_cls_name,
                    string="Animal sound"
                )

        """

        @api.multi
        @api.depends(field_name)
        def _compute_selection_field(rs):
            enumclass = self.resolve_enumclass(rs)
            for record in rs:
                value = getattr(record, field_name, None)
                if value is not None:
                    member = _get_member_by_value(enumclass, value)
                    setattr(record, selection_field_name, member.name)
                else:
                    setattr(record, selection_field_name, False)

        @api.multi
        def _set_selection(rs):
            enumclass = self.resolve_enumclass(rs)
            for record in rs:
                key = getattr(record, selection_field_name, None)
                if key:
                    member = _get_member_by_name(enumclass, key)
                    setattr(record, field_name, member.value)
                else:
                    setattr(record, field_name, False)

        if not compute_member_string:
            compute_member_string = self._default_compute_member_string
        kwargs.setdefault("store", False)
        kwargs.setdefault("compute", _compute_selection_field)
        kwargs.setdefault("inverse", _set_selection)
        return fields.Selection(
            selection=lambda s: [
                (name, compute_member_string(s, name, value))
                # Don't use `self.Enumclass`: when the selection field is
                # computed the setup_full may not be called yet.
                for name, value in self.resolve_enumclass(s).__members__.items()
            ],
            **kwargs,
        )

    @staticmethod
    def _default_compute_member_string(self, name, value):
        # The 'self' is actually a parameter that (the model); it's not a typo
        # and this function IS intentionally a staticmethod.
        return name

    def get_member_by_value(self, value, record=None):
        return _get_member_by_value(self.Enumclass, value)

    def get_member_by_name(self, name):
        return _get_member_by_name(self.Enumclass, name)

    def setup_full(self, model):
        # Injects a new class in the model MRO, so that we can guarantee
        # the expectation about the methods create, write and search.
        #
        # The alternative would be to implement pre_save and pre_search
        # receivers.  But that would run for ALL models regardless of the
        # presence of Enumeration fields.  Also, we need to rewrite the
        # argument in the 'search' method, and signals aren't designed for
        # such use case (although they work at the moment).
        #
        # We must find EnumerationAdapter in the MRO to avoid injecting it
        # twice when using Enumeration fields in abstract models.
        #
        # We don't need to inject the EnumerationAdapter in related
        # (delegated) copies for this Enumeration fields, because the
        # actual field does the right thing with DB (it does have the
        # EnumerationAdapter injected.)
        if self._setup_done != "full":
            cls = type(model)
            if EnumerationAdapter not in cls.mro() and not self.related:
                cls.__bases__ = (EnumerationAdapter,) + cls.__bases__
                logger.debug("Setting %s to model %s(%s, %s)", self, model, cls, id(cls))
            self.Enumclass = self.resolve_enumclass(model)
            result = super(Enumeration, self).setup_full(model)
            if not self.compute and not self.related and not model._abstract:
                assert self.name in model.fields_get()
            return result

    def _add_selection_field(self, model):
        if self.selection_field_kwargs:
            cls = type(model)
            selection_field_name = self.selection_field_kwargs.pop("name")
            if selection_field_name not in cls._fields and not self.related:
                selection_field = self.get_selection_field(
                    self.name, selection_field_name, **self.selection_field_kwargs
                )
                logger.debug("Adding %s to model %s", selection_field_name, model)
                model._add_field(selection_field_name, selection_field)

    def convert_to_read(self, value, record, use_name_get=True):
        if value is not None and value is not False:
            return self.get_member_by_value(value).value
        else:
            return value

    def convert_to_write(self, value, record):
        if value is not None and value is not False:
            if value in self.Enumclass.__members__.values():
                member = self.get_member_by_value(value)
                # Our EnumerationAdapter takes care of doing the right
                # thing when writing to the DB, also convert_to_column
                # does.
                return member.value
        return value

    def convert_to_cache(self, value, record, validate=True):
        if value not in self.Enumclass.__members__.values():
            if value is not None and value is not False:
                return self.get_member_by_name(value).value
        return value

    # NOTE: The parameter `values` was introduced in Odoo 11; the
    # parameter validate was introduced in Odoo 12.  We don't use
    # either; but declare them both to work across the three Odoo
    # versions.
    def convert_to_column(self, value, record, values=None, validate=True):
        if value in self.Enumclass.__members__.values():
            return Char.convert_to_column(self, self.get_member_by_value(value).name, record)
        else:
            return Char.convert_to_column(self, value, record)


class Adapter(object):
    # See the note in setup_full above.

    # Odoo 11 requires all bases to have these attributes.  See
    # odoo/models.py, method _build_model_attributes in lines 515-555 (at the
    # time of writing).
    _table = None
    _sequence = None
    _inherits = _depends = {}
    _sql_constraints = []
    _constraints = []
    _description = None

    # Odoo 12 requires this attribute.  See odoo/models.py, line 528
    _inherit = None


class EnumerationAdapter(Adapter):
    "Adapt the create/write/search method to Enumeration fields."

    @api.model
    @api.returns(*models.BaseModel.search._returns)
    def search(self, args, *pos_args, **kwargs):
        for index, query_part in enumerate(args):
            if not isinstance(query_part, str):
                fieldname, operator, operands = query_part
                field = self._fields.get(fieldname, None)
                if isinstance(field, Enumeration):
                    if operator in (
                        "=",
                        "!=",
                        "ilike",
                        "not ilike",
                        "like",
                        "not like",
                        "=like",
                        "=ilike",
                    ):
                        values = _get_db_value(field, operands)
                    elif operator in ("in", "not in"):
                        values = [_get_db_value(field, o) for o in operands]
                    else:
                        raise TypeError(
                            "Unsupported operator %r for an enumeration field" % operator
                        )
                    args[index] = (fieldname, operator, values)
        return super(EnumerationAdapter, self).search(args, *pos_args, **kwargs)

    @api.model_create_multi
    @api.returns("self", lambda value: value.id)
    def create(self, values):
        if isinstance(values, Mapping):
            values = {
                fieldname: _get_db_value(self._fields.get(fieldname, None), value)
                for fieldname, value in values.items()
            }
        else:
            values = [
                {
                    fieldname: _get_db_value(self._fields.get(fieldname, None), value)
                    for fieldname, value in vals.items()
                }
                for vals in values
            ]
        return super(EnumerationAdapter, self).create(values)

    @api.multi
    def write(self, values):
        for fieldname, value in dict(values).items():
            field = self._fields.get(fieldname, None)
            values[fieldname] = _get_db_value(field, value)
        return super(EnumerationAdapter, self).write(values)


def _get_db_value(field, value):
    if value is None or value is False:  # and not field.required
        return value
    if isinstance(field, Enumeration):
        member = field.get_member_by_value(value)
        return member.name
    else:
        return value


def _get_member_by_value(enumclass, value):
    """Find the enumclass's member that is equal to `value`."""
    try:
        return next(Member(k, v) for k, v in enumclass.__members__.items() if v == value)
    except StopIteration:
        raise ValueError("Invalid member %r of enumeration %r" % (value, enumclass)) from None


def _get_member_by_name(enumclass, name):
    """Find the enumclass's member by name"""
    try:
        return Member(name, enumclass.__members__[name])
    except (AttributeError, KeyError):
        raise ValueError("Invalid key %r of enumeration %r" % (name, enumclass)) from None


def constant(value):
    "Create a function (of many args) that always returns a constant `value`."

    def result(*args, **kwargs):
        return value

    return result


@api.model
def _setup_fields(self):
    cls = type(self)
    for field in dict(cls._fields).values():
        if isinstance(field, Enumeration):
            field._add_selection_field(self)
    _super_setup_fields(self)


_super_setup_fields = models.BaseModel._setup_fields
models.BaseModel._setup_fields = _setup_fields
