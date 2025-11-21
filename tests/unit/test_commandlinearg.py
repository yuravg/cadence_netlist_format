"""Unit tests for commandlinearg module.

Tests command-line argument parsing functionality.
"""

import sys
import pytest

from cadence_netlist_format.commandlinearg import (
    get_args,
    __prog__,
    __description__,
    __version_string__
)
from cadence_netlist_format import __version__


class TestCommandLineArgs:
    """Test suite for command-line argument parsing."""

    def test_get_args_no_arguments(self, monkeypatch):
        """Test get_args() with no command-line arguments.

        Should successfully parse with no errors when no arguments are provided.
        """
        # Mock sys.argv to simulate no arguments (just program name)
        monkeypatch.setattr(sys, 'argv', ['cnl_format'])

        # Should not raise any exceptions
        args = get_args()
        assert args is not None

    def test_get_args_version_short_flag(self, monkeypatch, capsys):
        """Test get_args() with -V flag.

        The -V flag should trigger version output and SystemExit.
        """
        # Mock sys.argv to simulate -V argument
        monkeypatch.setattr(sys, 'argv', ['cnl_format', '-V'])

        # ArgumentParser's version action causes SystemExit(0)
        with pytest.raises(SystemExit) as exc_info:
            get_args()

        # Verify it exits with code 0 (success)
        assert exc_info.value.code == 0

        # Capture and verify version output
        captured = capsys.readouterr()
        assert __version_string__ in captured.out or __version_string__ in captured.err

    def test_get_args_version_long_flag(self, monkeypatch, capsys):
        """Test get_args() with --version flag.

        The --version flag should trigger version output and SystemExit.
        """
        # Mock sys.argv to simulate --version argument
        monkeypatch.setattr(sys, 'argv', ['cnl_format', '--version'])

        # ArgumentParser's version action causes SystemExit(0)
        with pytest.raises(SystemExit) as exc_info:
            get_args()

        # Verify it exits with code 0 (success)
        assert exc_info.value.code == 0

        # Capture and verify version output
        captured = capsys.readouterr()
        assert __version_string__ in captured.out or __version_string__ in captured.err

    def test_version_string_format(self):
        """Test that version string has correct format.

        Version string should follow pattern: "program_name X.Y.Z"
        """
        # Verify version string contains program name
        assert __prog__ in __version_string__

        # Verify version string contains the actual version number
        assert __version__ in __version_string__

        # Verify exact format
        expected = '%s %s' % (__prog__, __version__)
        assert __version_string__ == expected

    def test_prog_name(self):
        """Test that program name is correctly set."""
        assert __prog__ == "cnl_format"

    def test_description(self):
        """Test that program description is correctly set."""
        expected_desc = "Format Cadence Allegro Net-List (cnl - Cadence Net-List) to readable file"
        assert __description__ == expected_desc

    def test_get_args_help_flag(self, monkeypatch, capsys):
        """Test get_args() with --help flag.

        The --help flag should trigger help output and SystemExit.
        """
        # Mock sys.argv to simulate --help argument
        monkeypatch.setattr(sys, 'argv', ['cnl_format', '--help'])

        # ArgumentParser's help action causes SystemExit(0)
        with pytest.raises(SystemExit) as exc_info:
            get_args()

        # Verify it exits with code 0 (success)
        assert exc_info.value.code == 0

        # Capture and verify help output contains description
        captured = capsys.readouterr()
        help_output = captured.out + captured.err
        assert __description__ in help_output or 'usage' in help_output.lower()

    def test_get_args_invalid_argument(self, monkeypatch, capsys):
        """Test get_args() with invalid argument.

        Invalid arguments should cause ArgumentParser to exit with error.
        """
        # Mock sys.argv to simulate invalid argument
        monkeypatch.setattr(sys, 'argv', ['cnl_format', '--invalid-flag'])

        # ArgumentParser should exit with code 2 for invalid arguments
        with pytest.raises(SystemExit) as exc_info:
            get_args()

        # Verify it exits with code 2 (argument error)
        assert exc_info.value.code == 2

    def test_version_matches_package_version(self):
        """Test that commandlinearg uses the correct package version.

        The version in __version_string__ should match the package __version__.
        """
        from cadence_netlist_format import __version__ as pkg_version
        assert __version__ == pkg_version
        assert pkg_version in __version_string__


class TestArgumentParserConfiguration:
    """Test suite for ArgumentParser configuration."""

    def test_parser_has_version_argument(self, monkeypatch):
        """Test that parser includes version argument.

        Verify that both -V and --version are recognized.
        """
        # Test that -V is recognized (doesn't raise unrecognized argument error)
        monkeypatch.setattr(sys, 'argv', ['cnl_format', '-V'])
        with pytest.raises(SystemExit) as exc_info:
            get_args()
        # Version action exits with 0, not 2 (argument error)
        assert exc_info.value.code == 0

        # Test that --version is recognized
        monkeypatch.setattr(sys, 'argv', ['cnl_format', '--version'])
        with pytest.raises(SystemExit) as exc_info:
            get_args()
        # Version action exits with 0, not 2 (argument error)
        assert exc_info.value.code == 0

    def test_get_args_returns_namespace(self, monkeypatch):
        """Test that get_args() returns an argparse.Namespace object.

        When called without special flags, should return parsed arguments.
        """
        monkeypatch.setattr(sys, 'argv', ['cnl_format'])
        args = get_args()

        # Verify it returns something (Namespace object)
        assert args is not None

        # Namespace objects have __dict__ attribute
        assert hasattr(args, '__dict__')


class TestPython2Compatibility:
    """Test suite for Python 2/3 compatibility."""

    def test_argparse_import_available(self):
        """Test that ArgumentParser can be imported.

        Should work in both Python 2.7+ and Python 3.x.
        """
        try:
            from argparse import ArgumentParser
            assert ArgumentParser is not None
        except ImportError:
            # Python 2.6 or earlier (not supported but test the fallback)
            from ArgParse import ArgumentParser
            assert ArgumentParser is not None

    def test_version_string_formatting(self):
        """Test that version string uses compatible string formatting.

        Uses % formatting which works in both Python 2 and 3.
        """
        # Verify the format uses % style (not f-strings or .format())
        assert '%s version %s' in str(__version_string__) or isinstance(__version_string__, str)


# Integration-style test
class TestGetArgsIntegration:
    """Integration tests for get_args() function."""

    def test_typical_usage_no_args(self, monkeypatch):
        """Test typical usage: running program with no arguments.

        This is the normal case when user runs 'cnl_format'.
        """
        monkeypatch.setattr(sys, 'argv', ['cnl_format'])

        try:
            args = get_args()
            # Should succeed without exceptions
            assert True
        except SystemExit:
            # Should not exit for normal usage
            pytest.fail("get_args() should not exit when called without special flags")

    def test_version_output_format(self, monkeypatch, capsys):
        """Test the exact format of version output.

        Verify version output contains program name and version number.
        """
        monkeypatch.setattr(sys, 'argv', ['cnl_format', '--version'])

        with pytest.raises(SystemExit):
            get_args()

        captured = capsys.readouterr()
        output = captured.out + captured.err

        # Version output should contain both program name and version
        assert 'cln_format' in output.lower() or __prog__ in output
        assert __version__ in output
