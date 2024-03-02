#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Copyright (c) Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can do what the LICENCE file allows you to.
#

"""Some tools to improve `OpenERP` security.

- :func:`reset_all_passwords`: to reset all passwords in a data-base.

- :func:`reset_invalid_passwords`: to reset all invalid passwords in a
  data-base.

Previous two functions uses `xotl.tools.crypto.generate_password` to generate
new passwords using as `pass_phrase` the user login, `level` means a
generation method.  Each level implies all other with an inferior numerical
value.  See `xotl.tools.crypto.generate_password` for more information about
defined constants of security level.

"""

from xotl.tools.crypto import DEFAULT_PASS_PHRASE_LEVEL as _DEF_LEVEL  # noqa
from xotl.tools.names import strlist as strs

__all__ = strs(
    "PASS_PHRASE_LEVEL_BASIC",
    "PASS_PHRASE_LEVEL_MAPPED",
    "PASS_PHRASE_LEVEL_MAPPED_MIXED",
    "PASS_PHRASE_LEVEL_MAPPED_DATED",
    "PASS_PHRASE_LEVEL_STRICT",
    "reset_all_passwords",
    "reset_invalid_passwords",
)
del strs


def _reset_passwords(self, security_level, verbose, check=None):
    """Internal module function to reset passwords in a data-base.

    This function is used by :func:`reset_all_passwords` and
    :func:`reset_invalid_passwords` functions.

      :param self: The res.user model.

      :param security_level: Numerical security level (the bigger the more
             secure).

      :param verbose: If True, print to ``stdout`` information of every
             password change.

      :param check: A function that checks if for a given user the password
             must be changed or not (if not given, is equivalent for True to
             all users).  It must has following definition::

               def check(self, cr, id, login):

             Where `self` is the ``res.users`` model, `cr` the active
             data-base cursor, `id` the user data-base id to check, and
             `login` the user login identifier.

    """
    from xotl.tools.crypto import generate_password
    from xotl.tools.future.codecs import safe_encode

    users = self.search([])
    for user in users:
        login = user.login
        if check is None or check(user):
            user.password = password = generate_password(login, security_level)
            if verbose:
                print(
                    safe_encode(
                        ">>> id: %(id)s, login: %(login)s, "
                        "name: %(name)s, "
                        "password: '%(password)s'"
                        % {
                            "id": user.id,
                            "login": user.login,
                            "name": user.name,
                            "password": password,
                        }
                    )
                )


def reset_all_passwords(self, security_level=_DEF_LEVEL, verbose=True):
    """Reset all passwords in a data-base.

    :param self: The res.users model.

    :param security_level: Numerical security level (the bigger the more
           secure).

    :param verbose: If True, print every change password to ``stdout``.

    This function can be used as::

      from xoeuf.security import reset_all_passwords
      reset_all_passwords(env['res.users'], security_level=2)

    See module documentation for more info.

    """
    _reset_passwords(self, security_level, verbose)


def reset_invalid_passwords(self, security_level=_DEF_LEVEL):
    """Reset all invalid passwords in a data-base.

    :param self: The res.users model.

    :param security_level: Numerical security level (the bigger the more
           secure).

    An invalid password is when it is the same as login name. Print
    information about all users with invalid passwords.

    This function can be used as::

      from xoeuf.security import reset_invalid_passwords
      reset_invalid_passwords(env['res.users'])

    See module documentation for more info.

    """

    def check(self):
        from odoo.exceptions import AccessDenied

        try:
            self.sudo(self.id).check_credentials(self.login)
            return True
        except AccessDenied:
            return False

    _reset_passwords(self, security_level, True, check)
