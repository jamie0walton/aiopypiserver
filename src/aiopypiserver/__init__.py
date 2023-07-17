"""Make `aiopypiserver` work."""
from .webserver import run

__all__ = []


def commandline_run():
    run()
