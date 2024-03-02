#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Copyright (c) Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can do what the LICENCE file allows you to.
#
from odoo.fields import Field as Base
from xotl.tools.symbols import Unset


class PropertyField(Base):
    """A property-like field.

    This is always non-store field.  In fact, you may only pass the getter,
    setter and deleter functions.

    .. warning:: This is a kind of hack.

       Normal Python `properties <property>`:class: are not copied through
       Odoo inheritance mechanisms.  This `Property` is a Field and Odoo
       accounts for it.  But, it is NOT an actual ORM field in the sense that
       it never interacts with the DB.  Therefore:

       - You MUST NEVER use ``write()`` or ``create()`` on these type of
         fields.  You may update the value via the `setter` (i.e assign it).

       - You cannot ``search()`` for this type of fields.

       - You cannot use Property fields in views.

         The main difference to any other computed field is that Property is
         untyped.  We don't enforce any type check on the value returned by
         getters.  But, then, we cannot communicate which widget can manage
         the value of a Property.

    The `getter`, `setter` and `deleter` functions receive (and thus we
    required it) a singleton recordset instance.  The `onsetup` function
    receive the field instance, and the model on which the field is being
    setup.

    Usage::

       @Property
       def result(self):
           return 1

       @result.setter
       def result(self, value):
          pass

       @Property(memoize=True)
       def sentinel(self):
           return object()

    You may also do::

       def _set_result(self, value):
           pass

       result = Property(lambda s: 1, setter=_set_result)
       del _set_result

    :keyword memoize: If True, the property will cache the result.  The
             default is False (compute each time the property is read).

    .. versionchanged:: 0.58.0 Added keyword parameter `memoize`.

    .. versionchanged:: 0.67.0 Invalidate Odoo's cache of dependant computable
       fields.

    .. versionchanged:: 0.68.0 Actively trigger recomputation on dependant
       fields.

    """

    # This is the best of the three major versions of Odoo we support.  This
    # create a __slot__ and avoids that these values go to the
    # __getattr__/__setattr__ mechanism in fields.Field.  But it also, means
    # that we need to do some tricks in the `__init__`:meth: to make all
    # versions happy.
    _slots = {
        "property_getter": None,
        "property_setter": None,
        "property_deleter": None,
        "property_onsetup": None,
        "memoize_result": False,
        "prefetch": False,  # There's no need to prefetch something that's not stored.
    }
    type = "python-property"  # needed to satisfy ir.models.field

    def __init__(self, getter, setter=None, deleter=None, onsetup=None, memoize=False, **kwargs):
        # Notice we don't abide by the expected fields signature.  Instead, we
        # require one that is compatible with `property`; but we ensure that
        # Odoo sees this Property as normal field with custom attributes.  We
        # allow for inheritance (_inherits) of this field.  Such inheritance
        # is done via a related field, but otherwise custom `write/create`
        # that treat properties could be ignored.
        kw = {
            "inherited": kwargs.get("inherited", None),
            "related": kwargs.get("related", None),
            "related_sudo": kwargs.get("related_sudo", False),
        }
        super(PropertyField, self).__init__(
            # Odoo ignores arguments which are None, therefore, let's force
            # them with Unset.  Odoo 9 and 10, uses this args to call
            # field.new(**args), and also to restore the values of the _slots
            # to provided values instead of default ones.  This last thing is
            # done when building the specific field for each Model Class (see
            # our `registry.rst`); cf. Field._setup_attrs.
            #
            # WARNING: If you remove this thinking that put those values just
            # a few lines below, you're fooling yourself.
            property_getter=getter or Unset,
            property_setter=setter or Unset,
            property_deleter=deleter or Unset,
            property_onsetup=onsetup or Unset,
            memoize_result=memoize,
            compute=getter,
            store=False,
            copy=False,
            **kw,
        )
        # In any case, we need those values now to make `new()` below work.
        self.property_getter = getter or Unset
        self.property_setter = setter or Unset
        self.property_deleter = deleter or Unset
        self.property_onsetup = onsetup or Unset
        self.memoize_result = memoize

    def new(self, **kwargs):
        # Ensure the property getter, setter and deleter are provided.  This
        # is used in `setter`:meth: and `deleter`:meth:.
        getter = kwargs.pop("getter", self.property_getter)
        setter = kwargs.pop("setter", self.property_setter)
        deleter = kwargs.pop("deleter", self.property_deleter)
        onsetup = kwargs.pop("onsetup", self.property_onsetup)
        memoize = kwargs.pop("memoize", self.memoize_result)
        return type(self)(
            getter=getter,
            setter=setter,
            deleter=deleter,
            onsetup=onsetup,
            memoize=memoize,
            **kwargs,
        )

    def setup_full(self, model):
        res = super(PropertyField, self).setup_full(model)
        if self.property_onsetup:
            self.property_onsetup(self, model)
        return res

    def setter(self, f):
        return self.new(setter=f)

    def deleter(self, f):
        return self.new(deleter=f)

    def onsetup(self, f):
        return self.new(onsetup=f)

    def get_related_instance(self, instance):
        related = self.args.get("related")
        if related and instance is not None:
            for x in related[:-1]:
                instance = instance[x]
        return instance

    def __get__(self, instance, owner):
        if instance is None:
            return self
        else:
            instance = self.get_related_instance(instance)
            if not instance:
                return self.null(instance.env)
            instance.ensure_one()
            if not self.memoize_result:
                return self.property_getter(instance)
            else:
                Unset = object()
                result = _get_from_cache(instance, self, Unset)
                if result is Unset:
                    result = self.property_getter(instance)
                    _set_to_cache(instance, self, result)
                return result

    def __set__(self, instance, value):
        instance = self.get_related_instance(instance)
        if self.property_setter:
            instance.ensure_one()
            self.property_setter(instance, value)
            # In normal Odoo fields, __set__ would call `write` to set the
            # value to the DB, and it is there where recomputation happens.
            # But we don't call write because Property is never stored in the
            # DB, so we need to trigger recomputations ourselves.
            self._cache_and_recompute_dependants(instance, value)
        else:
            raise TypeError("Setting to read-only Property")

    def __delete__(self, instance):
        instance = self.get_related_instance(instance)
        if self.property_deleter:
            instance.ensure_one()
            self.property_deleter(instance)
            self._cache_and_recompute_dependants(instance, Removed)
        else:
            raise TypeError("Deleting undeletable Property")

    # Since Odoo 11 (commit e25bcf41e2f312536a00ef8531b2f6c6e0334ebc), fields
    # no longer have a `modified()` method.  Instead they merged that into the
    # `modified()` method of models; but `BaseModel.modified()` calls the
    # invalidation of the cache without regards of our semantics for
    # memoization.
    #
    # So we need to reset the cache before triggering the recomputation of
    # dependant fields.
    def _cache_and_recompute_dependants(self, instance, value):
        instance.modified([self.name])
        if self.memoize_result:
            if value is not Removed:
                _set_to_cache(instance, self, value)
            # we don't need to call _del_from_cache because
            # `instance.modified` did it already.
        if instance.env.recompute and instance._context.get("recompute", True):
            instance.recompute()


class _PropertyType(type):
    def __instancecheck__(self, instance):
        return isinstance(instance, PropertyField)

    def __subclasscheck__(self, klass):
        return issubclass(klass, PropertyField)

    def __call__(self, getter=None, setter=None, deleter=None, onsetup=None, **kwargs):
        memoize = kwargs.pop("memoize", Unset)
        if memoize is Unset and getter is None:
            raise TypeError("getter must be provided")
        elif getter is None:

            def result(getter):
                return PropertyField(
                    getter,
                    setter=setter,
                    deleter=deleter,
                    onsetup=onsetup,
                    memoize=bool(memoize),
                    **kwargs,
                )

            return result
        else:
            return PropertyField(
                getter,
                setter=setter,
                deleter=deleter,
                onsetup=onsetup,
                memoize=bool(memoize),
                **kwargs,
            )


class Property(metaclass=_PropertyType):
    # So that isinstance(x, Property) work
    pass


Property.__doc__ = PropertyField.__doc__


def _get_from_cache(record, field, default):
    return record.env.cache.get_value(record, field, default)


def _set_to_cache(record, field, value):
    record.env.cache.set(record, field, value)


def _del_from_cache(record, field):
    record.env.cache.remove(record, field)


def _invalidate_cache(record, spec):
    record.env.cache.invalidate(spec)


# Sentinel object to know we're removing a key from the cache
Removed = object()
