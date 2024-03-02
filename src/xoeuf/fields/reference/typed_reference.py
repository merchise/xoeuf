#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Copyright (c) Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can do what the LICENCE file allows you to.
#
from odoo import _, api, fields, models

from xoeuf.models import iter_descendant_models
from xoeuf.osv.expression import Domain


def get_mixin_descendants(pool, mixin):
    """Get the models that inherit from `mixin`.

    :param mixin: mixin name to get it descendants.

    """
    yield from (
        modelname
        for modelname, _ in iter_descendant_models(
            pool, [mixin], find_delegated=False, allow_transient=True
        )
    )


class TypedReference(fields.Reference):
    """A reference field filtered by a type (mixin).

    This is like a Many2one field, but the comodel should be an AbstractModel
    (a mixin).  This way you can relate objects in different actual models but
    that share a common type.

    .. warning:: This field works only in Odoo 11+.

    .. warning:: Searching fields of a typed-reference, could be costly if
       there are many models that inherit from the mixin.  We issue a query
       per model in order to be able to find the references.

    """

    _slots = {"mixin": None, "comodel_name": None, "delegate": None}

    def __init__(self, mixin=fields.Default, delegate=fields.Default, **kwargs):
        # Set comodel_name = mixin, this is required for odoo make triggers
        # on delegate field declarations.
        super().__init__(**dict(kwargs, mixin=mixin, comodel_name=mixin, delegate=delegate))

    def new(self, **kwargs):
        # Pass original args to the new one.  This ensures that the
        # mixin arg is present.  In odoo/models.py, Odoo calls
        # this `new()` without arguments to duplicate the fields from parent
        # classes.
        kwargs = dict(self.args, **kwargs)
        return super().new(**kwargs)

    def _setup_regular_base(self, model):
        if not self.selection:

            def selection(model):
                return [
                    (model_name, _(model.env[model_name]._description or model_name))
                    for model_name in get_mixin_descendants(model.pool, self.mixin)
                ]

            self.selection = selection
        return super()._setup_regular_base(model)

    def convert_to_cache(self, value, record, validate=True):
        res = super().convert_to_cache(value, record, validate=validate)
        if res and validate:
            res_model, _res_id = res
            descendants = list(get_mixin_descendants(record.pool, self.mixin))
            if res_model not in descendants:
                raise ValueError(_("Wrong value for %s: %r") % (self, res))
        return res


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
    """Determine inherited fields."""
    # determine candidate inherited fields
    for reference_field_name, reference_field in reference_fields:
        mixin = self.env[reference_field.mixin]
        for name, field in mixin._fields.items():
            if name not in self._fields:
                # determine dependencies, compute, inverse, and search
                args = dict(
                    field.args,
                    compute=_make_compute_method(reference_field_name, name),
                    depends=(
                        reference_field_name,
                        "%s.%s" % (reference_field_name, name),
                    ),
                )
                if not (field.readonly or reference_field.readonly):
                    args["inverse"] = _make_inverse_method(reference_field_name, name)
                if field._description_searchable:
                    # allow searching on self only if the related
                    # field is searchable
                    args["search"] = _make_search_method(reference_field_name, name)
                # copy attributes from field to self (string, help, etc.)
                for attr, prop in field.related_attrs:
                    args[attr] = getattr(field, prop)
                # special case for states
                if field.states:
                    args["states"] = field.states
                # special case for required fields
                if field.required:
                    args["required"] = True
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

    return _set


def _make_search_method(reference_field, field_name):
    @api.multi
    def _search(self, operator, value):
        domain = Domain.FALSE
        for model in get_mixin_descendants(self.pool, self._fields[reference_field].mixin):
            for r in self.env[model].search([(field_name, operator, value)]):
                domain |= [(reference_field, "=", r.reference_repr)]
        return domain

    return _search


super_setup_base = models.BaseModel._setup_base
models.BaseModel._setup_base = _setup_base
models.BaseModel._add_inherits_by_reference_fields = _add_inherits_by_reference_fields
