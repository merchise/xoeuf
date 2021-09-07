#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Copyright (c) Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can do what the LICENCE file allows you to.
#
import os
import versioneer

from setuptools import setup, find_packages


# Import the version from the release module
project_name = "xoeuf"
_current_dir = os.path.dirname(os.path.abspath(__file__))


def safe_read(*paths):
    fname = os.path.join(_current_dir, *paths)
    try:
        with open(fname, "r") as fh:
            return fh.read()
    except OSError:
        return ""


setup(
    name=project_name,
    version=versioneer.get_version(),
    description="Basic utilities for OpenERP Open Object Services",
    long_description=safe_read("docs", "readme.txt"),
    cmdclass=versioneer.get_cmdclass(),
    # Get more strings from
    # http://pypi.python.org/pypi?:action=list_classifiers
    classifiers=[
        "Programming Language :: Python",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",  # noqa
        "Development Status :: 4 - Beta",
    ],
    keywords="openerp open-object server library".split(),
    author="Merchise Autrement [~º/~]",
    author_email="",
    url="http://www.merchise.org/",
    license="GPL",
    packages=find_packages(exclude=["ez_setup", "examples", "tests"]),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        "pytz",
        "decorator>=4.0,<4.2",
        "xotl.tools>=1.9.0,<2.3",
        'ipython<6; python_version < "3"',
        'ipython; python_version >= "3"',
        'enum34; python_version < "3.4"',
        "celery>=4.1.0,<6",
        'typing;python_version<"3.5"',
        "expiringdict~=1.2.0",
        'dataclasses;python_version<"3.7"',
    ],
    extra_requires={
        "odoo": ['odoo>=12.0,<13.0; python_version >= "3.5"'],
        "test": ["hypothesis>=3.7.0,<4"],
    },
    python_requires=">=3.6",
    entry_points="""
      [console_scripts]
      xoeuf = xoeuf.cli.server:server
      xoeuf_mailgate = xoeuf.cli.mailgate:main

      [xoeuf.addons]
      test_localized_dt = xoeuf.tests.test_localized_dt
      """,
)
