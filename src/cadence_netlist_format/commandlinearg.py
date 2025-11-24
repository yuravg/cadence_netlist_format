"""Get arguments from command line"""

from __future__ import annotations
from argparse import ArgumentParser, Namespace

from .__init__ import __version__

__prog__ = "cnl_format"
__description__ = "Format Cadence Allegro Net-List (cnl - Cadence Net-List) to readable file"
__version_string__ = f'{__prog__} {__version__}'


def get_args() -> Namespace:
    """Run Argument Parser and get argument from command line"""
    parser = ArgumentParser(prog=__prog__,
                            description=__description__)
    parser.add_argument('-V', '--version',
                        action='version',
                        version=__version_string__)
    return parser.parse_args()
