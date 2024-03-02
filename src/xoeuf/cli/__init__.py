# Makes sure modules are patched before any command-related code is
# invoked.
DEFAULT_COMMAND = "server"

from xotl.tools.cli import Command as BaseCommand  # noqa


class CommandsProxy(BaseCommand):
    """Define a proxy to register all OpenERP CLI commands to "xotl.tools.cli"."""

    __new__ = None  # Can't be instantiated

    @classmethod
    def __commands__(cls):
        """Get all OpenERP registered commands.

        Discard add-ons that raise errors when importing them.

        """
        name = "__commands_cache__"
        res = getattr(cls, name, None)
        if not res:
            from odoo.cli.command import commands
            from odoo.modules.module import initialize_sys_path

            cls._discover_addons_path()
            initialize_sys_path()
            res = commands
            setattr(cls, name, res)
        return res.values()

    @staticmethod
    def _discover_addons_path():
        import sys

        args = sys.argv[1:]
        prefix = "--addons-path="
        addons_path = next((a for a in args if a.startswith(prefix)), None)
        if addons_path:
            from odoo.tools import config

            config.parse_config([addons_path])


BaseCommand.set_default_command(DEFAULT_COMMAND)


class CommandType(type(BaseCommand)):
    def __new__(cls, name, bases, attrs):
        from xoeuf.api import contextual

        run = attrs.get("run", None)
        if run:
            attrs["run"] = contextual(run)
        return super(CommandType, cls).__new__(cls, name, bases, attrs)


class Command(BaseCommand, metaclass=CommandType):
    @staticmethod
    def invalidate_logging(base=None):
        """Force the logger `base` to report only CRITICAL messages.

        :param base: The name of logger to invalidate.  None is the root
                     logger *and* the "openerp" logger.

        """
        import logging

        logger = logging.getLogger(base)
        logger.setLevel(logging.CRITICAL)
        if not base:
            Command.invalidate_logging("openerp")


del BaseCommand


# TODO: Loader?
from . import addons as _addons  # noqa
from . import migration  # noqa
from . import secure as _secure  # noqa

del _secure, _addons, migration
