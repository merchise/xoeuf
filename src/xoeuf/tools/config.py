#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Copyright (c) Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can do what the LICENCE file allows you to.
#

"""Xœuf Configuration Service.

Define the class :class:`MetaOptions` which is a singleton that wraps
``openerp.tools.config``, it's instanced automatically at the end of this
module.

If Xœuf Services are called from an application with arguments, they are parsed
and loaded the first time this module is used.

If a command is invoked, it's looked in all OpenERP configured modules (addons)
and its arguments are parsed and it's executed.

You can update or load all options by calling in any time either the method
:meth:`!options.load` or the method :meth:`!options.update`.

"""

from collections import MutableMapping

DEFAULT_COMMAND = str("server")
_SECTION_SEP = str(".")


class MetaOptions(type):
    __singleton__ = None

    def __new__(cls, name, bases, attrs):
        if cls.__singleton__ is None:
            from odoo.tools import config

            attrs["__new__"] = None  # can't be instantiated!
            attrs["wrapped"] = config
            self = super(MetaOptions, cls).__new__(cls, name, bases, attrs)
            cls.__singleton__ = self
            return self
        else:
            msg = (
                "Only one configuration instance allowed:\n"
                '\tdefining "%s", already defined "%s"!'
            )
            TypeError(msg % (name, cls.__singleton__.__name__))

    def __dir__(self):
        return list(self.wrapped.options) + list(self.__dict__)

    def __hash__(self):
        from xotl.tools.names import nameof

        return hash(nameof(self, inner=True, full=True))

    def __eq__(self, other):
        return other is self

    def __ne__(self, other):
        return not (self == other)

    def __len__(self):
        res = len(self.wrapped.options)
        for section in self.wrapped.misc:
            res += len(self.wrapped.misc[section])
        return res

    def __contains__(self, option):
        if _SECTION_SEP in option:
            section, option = option.split(_SECTION_SEP)
            return option in self.wrapped.misc.get(section, {})
        else:
            return option in self.wrapped.options

    def __iter__(self):
        for option in self.wrapped.options:
            yield option
        for section in self.wrapped.misc:
            for option in self.wrapped.misc[section]:
                yield _SECTION_SEP.join((section, option))

    def __getitem__(self, option):
        if _SECTION_SEP in option:
            section, option = option.split(_SECTION_SEP)
            return self.wrapped.misc[section][option]
        else:
            return self.wrapped[option]

    def __setitem__(self, option, value):
        if isinstance(option, str):
            option = str(option)
            if value in ("True", "true"):
                value = True
            elif value in ("False", "false"):
                value = False
            elif value == "None":
                value = None
            if _SECTION_SEP in option:
                section, option = option.split(_SECTION_SEP)
                self.wrapped.misc[section][option] = value
            else:
                self.wrapped[option] = value
        else:
            msg = 'option name must be str, "%s" of type "%s" is provided!'
            raise TypeError(msg % (option, type(option).__name__))

    def __delitem__(self, option):
        if _SECTION_SEP in option:
            section, option = option.split(_SECTION_SEP)
            del self.wrapped.misc[section][option]
        elif option not in self.wrapped.casts:
            del self.wrapped.options[option]
        else:
            raise KeyError('read only option "%s"!' % option)

    def __getattr__(self, name):
        from xotl.tools.symbols import Unset

        res = self.wrapped.options.get(name, Unset)
        if res is not Unset:
            return res
        else:
            msg = "'%s' has no attribute '%s'"
            raise AttributeError(msg % (self.__name__, name))

    def __setattr__(self, name, value):
        if name not in self.__dict__ and name in self.wrapped.options:
            self[name] = value
        else:
            super(MetaOptions, self).__setattr__(name, value)

    def get(self, option, default=None):
        """returns options[option] if option in options, else default

        default is None if not given.

        """
        if _SECTION_SEP in option:
            from xotl.tools.symbols import Unset

            section, option = option.split(_SECTION_SEP)
            misc = self.wrapped.misc.get(section, Unset)
            return default if misc is Unset else misc.get(option, default)
        else:
            return self.wrapped.options.get(option, default)

    def keys(self):
        """return a set-like object providing a view on options' keys"""
        from collections import KeysView

        return KeysView(self)

    def items(self):
        """return a set-like object providing a view on options' items"""
        from collections import ItemsView

        return ItemsView(self)

    def values(self):
        """return an object providing a view on options' values"""
        from collections import ValuesView

        return ValuesView(self)

    def pop(self, option, *args):
        """options.pop(option[,default]) -> remove specified option name and
        return the corresponding option value.

        If option is not found, default is returned if given, otherwise
        KeyError is raised.
        """
        count = len(args)
        if count <= 1:
            from xotl.tools.symbols import Unset

            default = Unset if count == 0 else args[0]
            if _SECTION_SEP in option:
                section, option = option.split(_SECTION_SEP)
                misc = self.wrapped.misc.get(section, Unset)
                if misc is not Unset:
                    if default is Unset:
                        return misc.pop(option)
                    else:
                        return misc.pop(option, default)
                else:
                    raise KeyError(option)
            else:
                if default is Unset:
                    return self.wrapped.options.pop(option)
                else:
                    return self.wrapped.option.pop(option, default)
        else:
            msg = "pop expected at most 2 arguments, got %s"
            raise TypeError(msg % count + 1)

    def update(self, *args, **kwargs):
        """Update options from dict/iterable or keyword arguments

        If a positional argument (other) is present:

          - If has a "keys" method, does::
            for option in other:
                options[option] = other[option]

          - If not, does::
            for option, value in other:
                options[option] = value

        In either case, this is followed by::
            for option in kwargs:
                options[option] = kwargs[option]

        """
        count = len(args)
        if count <= 1:
            if args:
                other = args[0]
                if hasattr(other, "keys"):
                    for option in other:
                        self[option] = other[option]
                else:
                    for option, value in other:
                        self[option] = value
            for option in kwargs:
                self[option] = kwargs[option]
        else:
            msg = "update expected at most 1 positional argument, got %s"
            raise TypeError(msg % count)

    def setdefault(self, option, *args):
        """return options.get(`option`, `default`)

        also set options[`option`] = `default` if `option` not in options

        if `default` is not given, will try to find the default value
        configured, is not an standard option, then will use None.
        """
        count = len(args)
        if count <= 1:
            from xotl.tools.symbols import Unset

            default = Unset if count == 0 else args[0]
            if _SECTION_SEP in option:
                default = None if count == 0 else args[0]
                section, option = option.split(_SECTION_SEP)
                return self.wrapped.misc[section].setdefault(option, default)
            else:
                if count == 0:
                    opt = self.wrapped.casts.get(option)
                    default = opt.my_default if opt else None
                else:
                    default = args[0]
                return self.wrapped.options.setdefault(option, default)
        else:
            msg = "setdefault expected at most 2 arguments, got %s"
            raise TypeError(msg % count + 1)


MutableMapping.register(MetaOptions)


class options(metaclass=MetaOptions):
    """The single instance of :class:`MetaOptions` that wraps
    ``openerp.tools.config``.

    """


del MutableMapping
