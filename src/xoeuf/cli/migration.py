#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Copyright (c) Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can do what the LICENCE file allows you to.
#
import argparse
import io
import os
import pprint
import textwrap

from odoo import SUPERUSER_ID
from odoo.fields import Date, date
from odoo.modules.module import get_module_path

from . import Command

MIGRATION_TEMPLATE = """#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# ---------------------------------------------------------------------
# {migration_name}
# ---------------------------------------------------------------------
# Copyright (c) {current_year} Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the LICENCE attached (see LICENCE file) in the distribution
# package.
#
# Created on {today}

'''{migration_readable_name}

'''


CURRENT_MODULE = '{current_module}'
SOURCE_MODULE = '{source_module}'
FIELDS = {fields}

def migrate(cr, version):
    if version:
        cr.execute(
            '''
            UPDATE ir_model_data
            SET module=%(CURRENT_MODULE)s
            WHERE module=%(SOURCE_MODULE)s AND model='ir.model.fields' AND
            name NOT IN (SELECT name
                         FROM ir_model_data
                         WHERE module=%(CURRENT_MODULE)s) AND
            name IN %(FIELDS)s
            ''',
            {{
                'CURRENT_MODULE': CURRENT_MODULE,
                'SOURCE_MODULE': SOURCE_MODULE,
                'FIELDS': FIELDS
            }}
        )
        cr.commit()
"""

INPUT_VALID_VALUES = [
    (True, ("y", "ye", "yes", "s", "si", "sí")),
    (False, ("n", "no", "")),
]


def newline():
    print("")


def write(msg):
    print(msg)


def read_bool_value(prompt=None):
    _input = input(prompt)
    _input = _input.lower()
    for result, valid_values in INPUT_VALID_VALUES:
        if _input in valid_values:
            return result
    raise ValueError("Invalid option.")


def make_reference_name(field):
    """Get ir_model_data name generated for given model-field pair."""
    return "field_%s_%s" % (field[0].replace(".", "_"), field[1])


def get_fields(db, src):
    """Get all fields created on `src` module."""
    with db(transactional=True) as cr:
        cr.execute(
            """
            SELECT model, name
            FROM ir_model_fields
            WHERE id IN (
                SELECT res_id
                FROM ir_model_data
                WHERE module=%s AND model='ir.model.fields')
            ORDER BY model, name
        """,
            (src.module_name,),
        )
        for field in cr.fetchall():
            yield (make_reference_name(field), field)


def _get_content(src, dst, file_name, fields):
    fields_pretty_print = io.BytesIO()
    pprint.pprint(tuple(fields), stream=fields_pretty_print)
    name = textwrap.fill(
        "Migrate (some) fields reference from %s to %s" % (src.module_name, src.module_name),
        78,
    )
    today = date.today()
    return MIGRATION_TEMPLATE.format(
        migration_name=file_name,
        current_year=today.year,
        today=Date.to_string(today),
        migration_readable_name=name,
        source_module=src.module_name,
        current_module=dst.module_name,
        fields=fields_pretty_print.getvalue(),
    )


def write_migration(file_path, file_name, content):
    if not os.path.exists(file_path):
        os.makedirs(file_path)
    with open(file_path + file_name, "wb") as f:
        f.write(content)


def check_fields(fields, valid_fields):
    if fields[0].lower() in ("a", "all"):
        result = [ref for ref, _ in valid_fields]
    else:
        result = []
        for field in fields:
            field = field.strip().rsplit(".", 1)
            if field and len(field) == 2:
                ref = make_reference_name(field)
                result.append(ref)
                if (ref, tuple(field)) not in valid_fields:
                    raise ValueError("Given field (%s, %s) is not valid." % field[-1])
    return result


class Migration(Command):
    """Generates a migration file to move field references from a module to
    an other.

    """

    @classmethod
    def _get_arg_parser(cls):
        res = getattr(cls, "_arg_parser", None)
        if not res:
            res = argparse.ArgumentParser()
            cls._arg_parser = res
            res.add_argument(
                "-d",
                "--database",
                dest="database",
                required=True,
                type=DB,
                help="Name of the database used used to check actual status.",
            )
            res.add_argument("src_module", type=Module, help="Name of the source module")
            res.add_argument("dst_module", type=Module, help="Name of the destination module")
            res.add_argument(
                "-f",
                "--fields",
                dest="fields",
                nargs="+",
                help="Field to migrate on comma separated model.field "
                "format or `All` for all fields.",
            )
        return res

    def run(self, args):
        parser = self._get_arg_parser()
        options = parser.parse_args(args)
        options.src_module.load_module(options.database)
        options.dst_module.load_module(options.database)
        if options.fields:
            fields = check_fields(
                options.fields,
                list(get_fields(options.database.db, options.src_module)),
            )
        else:
            fields = []
            newline()
            write(
                "Press y/n to select what fields include on migration. "
                "Yes response must be explicit (<Enter> means no)."
            )
            for ref, model_field in get_fields(options.database.db, options.src_module):
                if read_bool_value("Model: %s; Field: %s >>> " % model_field):
                    fields.append(ref)
        if not fields:
            raise ValueError("No field selected")
        file_name = options.dst_module.get_file_name(options.src_module)
        content = _get_content(options.src_module, options.dst_module, file_name, fields)
        try:
            write_migration(options.dst_module.get_migration_path(), file_name, content)
        except Exception as e:
            write(str(e))
            newline()
            write(
                "\nCopy following lines and create manually "
                "the corresponding migration with this content."
            )
            write(content)
        else:
            write("Migration is created successfully.")


class DB(object):
    def __init__(self, db_name):
        import importlib

        py_module = "xoeuf.pool.%s" % db_name
        self.db = importlib.import_module(py_module)


class Module(object):
    def __init__(self, module_name):
        self.module_name = module_name
        self.module_path = get_module_path(module_name, display_warning=False)
        self.new_version = None
        self.module = None

    def __getattr__(self, item):
        if item in self.__dict__:
            return self.__dict__.get(item)
        else:
            return getattr(self.module, item)

    def get_migration_path(self):
        return "%s/migrations/%s/" % (self.module_path, self.new_version)

    def get_file_name(self, src):
        """Get a valid file name for the migration module."""
        base_name = "pre-migrate_fields_reference_from_%s_to_%s" % (
            src.module_name,
            self.module_name,
        )
        name = base_name
        count = 0
        while os.path.exists(self.get_migration_path() + name + ".py"):
            count += 1
            name = base_name + str(count)
        return name + ".py"

    def load_module(self, db):
        with db.db(transactional=True) as cr:
            obj = db.db.models.ir_module_module
            m_id = obj.search(cr, SUPERUSER_ID, [("name", "=", self.module_name)], limit=1)
            if m_id:
                module = obj.browse(cr, SUPERUSER_ID, m_id)
            if not module:
                raise ValueError("Not found module %s." % self.module_name)
            if module.state == "uninstalled":
                raise ValueError("Module %s is not already installed." % self.module_name)
            write(module.state + module.latest_version)
            self.module = module
            self.get_new_version()

    def get_new_version(self):
        if self.latest_version:
            current_version = list(self.latest_version.split("."))
            try:
                minor_version = int(current_version[-1])
                current_version[-1] = str(minor_version + 1)
            except ValueError:
                current_version.append("1")
            self.new_version = ".".join(current_version)


def main():
    from xotl.tools.cli import command_name
    from xotl.tools.cli.app import main

    main(default=command_name(Migration))


if __name__ == "__main__":
    main()
