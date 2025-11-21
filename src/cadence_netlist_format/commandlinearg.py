"""Get arguments from command line
"""

try:
    from argparse import ArgumentParser
except ImportError:  # for version < 3.0 (though argparse is available in 2.7+)
    # Note: argparse has been standard library since Python 2.7
    # This fallback should never be needed for supported Python versions
    from argparse import ArgumentParser

from .__init__ import __version__

__prog__ = "cnl_format"
__description__ = "Format Cadence Allegro Net-List (cnl - Cadence Net-List) to readable file"
__version_string__ = '%s %s' % (__prog__, __version__)


def get_args():
    """Run Argument Parser and get argument from command line"""
    parser = ArgumentParser(prog=__prog__,
                            description=__description__)
    parser.add_argument('-V', '--version',
                        action='version',
                        version=__version_string__)
    return parser.parse_args()
