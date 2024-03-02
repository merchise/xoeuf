#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Copyright (c) Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can do what the LICENCE file allows you to.
#
"""Tools for "Query Language".

Most of this has been extracted from `xotl.ql` (but we must support Python
2.7).

"""

import ast as pyast
import sys
from dataclasses import dataclass
from types import new_class

_py_version = sys.version_info
_py3 = _py_version >= (3, 0)
del sys


# For each AST class in the Python ast module we build a new one here that
# supports equality comparison::
#
#    qst.Name('a', qst.Load()) == qst.Name('b', qst.Load())
#
class PyASTNode(object):
    def __eq__(self, other):
        from operator import eq

        Unset = object()  # xotl.tools's Unset is equal to 0!
        res = True
        i = 0
        # Explicitly deal with NameConstant None.
        if is_constant(self, None):
            return other is None or is_constant(other, None) or other == LOAD_NONE
        elif is_constant(other, None):
            return self is None or self == LOAD_NONE
        attrs = self._fields
        if not attrs:
            # If no attrs only check for typing, both should have the same
            # name (_ast.Load and qst.Load, etc.) and one must a subclass of
            # the other.
            self, other = type(self), type(other)
            attrs = ("__name__",)
            res = issubclass(self, other) or issubclass(other, self)
        get_from_source = lambda a: getattr(self, a, Unset)  # noqa
        get_from_target = lambda a: getattr(other, a, Unset)  # noqa
        while res and (i < len(attrs)):
            attr = attrs[i]
            sattr = get_from_source(attr)
            tattr = get_from_target(attr)
            if eq(sattr, tattr):
                i += 1
            elif sattr is Unset or tattr is Unset:
                res = False
            elif sattr is None and tattr == LOAD_NONE or tattr == NONE_CT:
                i += 1
            elif tattr is None and sattr == LOAD_NONE or sattr == NONE_CT:
                i += 1
            else:
                res = False
        return res

    __hash__ = None

    def __str__(self):
        def r(who):
            if isinstance(who, pyast.AST):
                return "<ast: %s>" % type(who).__name__
            else:
                return repr(who)

        res = []
        children = [(self, None, 0)]
        while children:
            child, field, depth = children.pop(0)
            if field:
                res.append(" " * 3 * depth + "{}: ".format(field) + r(child))
            else:
                res.append(" " * 3 * depth + r(child))
            fields = getattr(child, "_fields", [])
            grandchildren = [(getattr(child, f, Missing(f)), f, depth + 1) for f in fields]
            if grandchildren:
                # If any grandchild is a list 'expand it', this helps to get a
                # nicer visualization.
                i = 0
                while i < len(grandchildren):
                    val, f, d = grandchildren[i]
                    if isinstance(val, (list, tuple)):
                        j = len(val)
                        grandchildren[i : i + 1] = [
                            (v, f + "[%d]" % k, d) for k, v in enumerate(val)
                        ]
                        i += j
                    else:
                        i += 1
                children[0:0] = grandchildren
        return "\n".join(res)

    @classmethod
    def from_pyast(cls, node):
        """Convert an `ast.AST`:py:class: node into the equivalent qst node."""

        def _convert(value):
            if value:
                type_ = globals().get(type(value).__name__, None)
                if type_:
                    value = type_.from_pyast(value)
            return value

        assert cls.__name__ == type(node).__name__
        res = cls()
        for attr in node._attributes:
            setattr(res, attr, getattr(node, attr, None))
        for field in node._fields:
            value = getattr(node, field, None)
            if isinstance(value, list):
                value = [_convert(val) for val in value]
            elif isinstance(value, tuple):
                value = tuple(_convert(val) for val in value)
            else:
                value = _convert(value)
            setattr(res, field, value)
        return res


__all__ = []
_nodes = [
    pyast.Expression,
    pyast.expr,
    pyast.boolop,
    pyast.unaryop,
    pyast.keyword,
    pyast.slice,
    pyast.operator,
    pyast.cmpop,
    pyast.comprehension,
    pyast.arguments,
    pyast.expr_context,
]

if _py3:
    _nodes.append(pyast.arg)

_current = 0
while _current < len(_nodes):
    _node = _nodes[_current]
    _more = _node.__subclasses__()  # Don't place this after the new class.

    globals()["_PyAst_%s" % _node.__name__] = _node
    # Has a constructor create the class for comparing
    globals()[_node.__name__] = cls = new_class(_node.__name__, bases=(_node, PyASTNode))
    cls.__module__ = "qst"
    __all__.append(_node.__name__)

    if _more:
        _nodes.extend(_more)
    _current += 1

if (3, 6) <= _py_version:
    # In Python 3.6+:
    #
    #      comprehension = (expr target, expr iter, expr* ifs, int is_async)
    #
    # I don't think this async stuff will impact the byte-code of a normal
    # query-like comprehension.
    #
    class comprehension(comprehension):  # noqa
        def __init__(self, *args):
            if 0 < len(args) < 4:
                args += (False,)
            super().__init__(*args)


# This None as a name.  Only use this for comparison, not as a return value.
LOAD_NONE = Name("None", Load())  # noqa

try:
    NONE_CT = NameConstant(None)  # noqa
except NameError:

    class NameConstant(object):
        def __init__(self, value):
            self.value = value

        def __eq__(self, other):
            return is_constant(other, self.value)

    NONE_CT = NameConstant(None)


def is_constant(which, value):
    "Test if which is a NameConstant for `value`."
    return isinstance(which, NameConstant) and which.value is value  # noqa


def parse(source, filename="<unknown>", mode="eval"):
    assert mode == "eval"
    res = pyast.parse(source, filename, mode)
    return Expression.from_pyast(res)  # noqa


def ensure_compilable(st):
    visitor = SetAttributesVisitor(lineno=1, col_offset=0)
    visitor.visit(st)
    return st


class SetAttributesVisitor(pyast.NodeVisitor):
    def __init__(self, **attrs):
        self.attrs = attrs

    def generic_visit(self, node):
        from xotl.tools.symbols import Unset

        get = lambda a: getattr(node, a, Unset)  # noqa
        for attr, val in self.attrs.items():
            if get(attr) is Unset:
                setattr(node, attr, val)
        return super(SetAttributesVisitor, self).generic_visit(node)


def make_argless_call(fn):
    return make_call(fn)


def make_call(fn, *args, **kwargs):
    kws = [keyword(name, val) for name, val in kwargs.items()]  # noqa
    if _py3:
        return Call(fn, list(args), kws)  # noqa
    else:
        return Call(fn, list(args), kws, None, None)  # noqa


def make_arguments(*names):
    assert _py3
    if (3, 4) <= _py_version < (3, 8):
        return arguments(  # noqa
            args=[arg(name, None) for name in names],  # noqa
            vararg=None,
            kwonlyargs=[],
            kw_defaults=[],
            kwarg=None,
            defaults=[],
        )
    if (3, 8) <= _py_version:
        return arguments(  # noqa
            posonlyargs=[],
            args=[arg(name, None, None) for name in names],  # noqa
            vararg=None,
            kwonlyargs=[],
            kw_defaults=[],
            kwarg=None,
            defaults=[],
        )
    else:
        assert False  # pragma: no cover


def make_attr(node, attr):
    return Attribute(node, attr, Load())  # noqa


@dataclass
class Missing:
    name: str
