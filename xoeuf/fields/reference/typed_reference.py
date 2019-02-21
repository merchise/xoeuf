#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Copyright (c) Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can do what the LICENCE file allows you to.
#

from __future__ import (division as _py3_division,
                        print_function as _py3_print,
                        absolute_import as _py3_abs_import)

from xoeuf.odoo import api, fields, models, _


def get_mixin_descendants(pool, mixin):
    ''' Get the models that inherit from `mixin`.

    :param mixin: mixin name to get it descendants.

    '''
    for model_name in pool.descendants([mixin], '_inherit'):
        if not pool[model_name]._abstract:
            yield model_name


class TypedReference(fields.Reference):
    '''A reference field filtered by type (mixin).

    Many2one equivalent recordset.

    '''
    type = 'reference'
    _slots = {
        'mixin': None,
        'delegate': None,
    }

    def __init__(self, mixin=fields.Default, delegate=fields.Default, **kwargs):
        super(TypedReference, self).__init__(
            mixin=mixin,
            delegate=delegate,
            **kwargs
        )

    def new(self, **kwargs):
        # Pass original args to the new one.  This ensures that the
        # mixin arg is present.  In odoo/models.py, Odoo calls
        # this `new()` without arguments to duplicate the fields from parent
        # classes.
        kwargs = dict(self.args, **kwargs)
        return super(TypedReference, self).new(**kwargs)

    def _setup_regular_base(self, model):
        def selection(model):
            return [
                (model_name, _(model.env[model_name]._description or model_name))
                for model_name in get_mixin_descendants(model.pool, self.mixin)
            ]
        if self.selection:
            descendants = [val for val, string in selection(model)]
            for val in self.get_values(model.env):
                if val not in descendants:
                    raise ValueError(
                        _("Wrong value for %s: %r") % (self, val)
                    )
        else:
            self.selection = selection
        return super(TypedReference, self)._setup_regular_base(model)


@api.model
def _setup_base(self, *args, **kwargs):
    super_setup_base(self, *args, **kwargs)
    delegate_reference_fields = {
        field.mixin: (name, field)
        for name, field in self._fields.items()
        if isinstance(field, TypedReference) and field.delegate
    }
    self._add_inherits_by_reference_fields(delegate_reference_fields.values())


@api.model
def _add_inherits_by_reference_fields(self, reference_fields):
    """ Determine inherited fields. """
    # determine candidate inherited fields
    for reference_field_name, reference_field in reference_fields:
        mixin = self.env[reference_field.mixin]
        for name, field in mixin._fields.items():
            if name not in self._fields:
                args = dict(
                    field.args,
                    compute=_make_compute_method(
                        reference_field_name,
                        name
                    ),
                    depends=(
                        reference_field_name,
                        '%s.%s' % (reference_field_name, name)
                    )
                )
                # determine dependencies, compute, inverse, and search
                if not (field.readonly or reference_field.readonly):
                    args['inverse'] = _make_inverse_method(
                        reference_field_name,
                        name
                    )
                if field._description_searchable:
                    # allow searching on self only if the related
                    # field is searchable
                    args['search'] = _make_search_method(
                        reference_field_name,
                        name
                    )
                self._add_field(name, field.new(**args))


def _make_compute_method(reference_field, field_name):
    @api.multi
    def _get(self):
        for record in self:
            reference = record[reference_field]
            if reference:
                record[field_name] = reference[field_name]
    return _get


def _make_inverse_method(reference_field, field_name):
    @api.multi
    def _set(self):
        for record in self:
            reference = record[reference_field]
            if reference:
                reference[field_name] = record[field_name]
            else:
                raise ValueError("TODO")
    return _set


def _make_search_method(reference_field, field_name):
    @api.multi
    def _search(self, operator, value):
        return [('%s.%s' % (reference_field, field_name), operator, value)]
    return _search


super_setup_base = models.BaseModel._setup_base
models.BaseModel._setup_base = _setup_base
models.BaseModel._add_inherits_by_reference_fields = _add_inherits_by_reference_fields
