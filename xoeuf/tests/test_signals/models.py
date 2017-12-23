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


# BEWARE that we test xoeuf implementation of signals, that's the reason of
# this import.
import xoeuf._signals_impl as signals

from xoeuf import models, fields


class SignalingModel(models.Model):
    _name = 'test_signals.signaling_model'

    name = fields.Char()


@signals.receiver(signals.post_save, sender='test_signals.signaling_model')
def do_nothing(sender, signal, **kwargs):
    pass


@signals.receiver(signals.pre_save, sender='test_signals.signaling_model')
def do_nothing_again(sender, signal, **kwargs):
    pass


@signals.wrapper(signals.write_wrapper, sender='test_signals.signaling_model')
def wrap_nothing(sender, wrapping, *args, **kwargs):
    yield