"""Pytest configuration and shared fixtures for cadence_netlist_format tests."""

import os
import pytest
import tempfile
import shutil


@pytest.fixture
def temp_dir(tmp_path):
    """Provide a temporary directory for test files.

    Args:
        tmp_path: pytest's built-in tmp_path fixture

    Returns:
        Path to temporary directory
    """
    return tmp_path


@pytest.fixture
def sample_netlist_path():
    """Path to sample netlist file in tests/data/inputs/ directory.

    Returns:
        str: Path to pstxnet_v1.dat
    """
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(project_root, 'tests', 'data', 'inputs', 'pstxnet_v1.dat')


@pytest.fixture
def sample_netlist_v1_path():
    """Path to sample netlist file version 1.

    Returns:
        str: Path to pstxnet_v1.dat
    """
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(project_root, 'tests', 'data', 'inputs', 'pstxnet_v1.dat')


@pytest.fixture
def sample_netlist_v2_path():
    """Path to sample netlist file version 2.

    Returns:
        str: Path to pstxnet_v2.dat
    """
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(project_root, 'tests', 'data', 'inputs', 'pstxnet_v2.dat')


@pytest.fixture
def sample_netlist_v3_path():
    """Path to sample netlist file version 3.

    Returns:
        str: Path to pstxnet_v3.dat
    """
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(project_root, 'tests', 'data', 'inputs', 'pstxnet_v3.dat')


@pytest.fixture
def temp_config_file(temp_dir):
    """Create a temporary config file for testing.

    Args:
        temp_dir: Temporary directory fixture

    Returns:
        str: Path to temporary config file
    """
    config_path = os.path.join(str(temp_dir), '.cnl_format.dat')
    return config_path


@pytest.fixture
def sample_config_data():
    """Provide sample configuration data.

    Returns:
        dict: Sample configuration dictionary
    """
    return {
        'Configuration': {
            'netlist_file': '/path/to/netlist.dat'
        },
        'Info': {
            'Description': 'Test configuration file'
        }
    }


@pytest.fixture
def simple_netlist_data():
    """Provide simple netlist data for testing.

    Returns:
        str: Simple netlist file content
    """
    return """FILE_TYPE = EXPANDEDNETLIST;
{ Using PSTWRITER 16.3.0 p002Apr-26-2016 at 14:52:09 }
NET_NAME
'TEST_NET'
 '@CAPTURENAME.sometext':
 C_SIGNAL='some_text';
NODE_NAME	R1 1
 '@CAPTURENAME.sometext':
 'PIN1':;
NODE_NAME	R2 2
 '@CAPTURENAME.sometext':
 'PIN2':;
END.
"""


@pytest.fixture
def change_to_temp_dir(temp_dir, monkeypatch):
    """Change working directory to temp_dir for the test.

    Args:
        temp_dir: Temporary directory fixture
        monkeypatch: pytest monkeypatch fixture
    """
    monkeypatch.chdir(str(temp_dir))
    return temp_dir


# Test count validation hook
def get_expected_test_count():
    """Read expected test count from pyproject.toml.

    Returns:
        int: Expected number of tests, or None if not configured
    """
    try:
        import tomllib
    except ImportError:
        import tomli as tomllib  # type: ignore

    try:
        with open('pyproject.toml', 'rb') as f:
            data = tomllib.load(f)
            return data.get('tool', {}).get('cadence_netlist_format', {}).get('testing', {}).get('expected_test_count')
    except (FileNotFoundError, KeyError):
        return None


@pytest.hookimpl(tryfirst=True)
def pytest_collection_finish(session):
    """Validate test count after collection.

    This hook runs after pytest collects all tests but before execution.
    Validates that collected test count matches expected count in pyproject.toml.

    Args:
        session: pytest session object containing collected items

    Raises:
        pytest.UsageError: If test count doesn't match expected count
    """
    expected_count = get_expected_test_count()

    if expected_count is None:
        # Not configured - skip validation
        return

    collected_count = len(session.items)

    if collected_count != expected_count:
        msg = (
            f"\n{'='*70}\n"
            f"TEST COUNT VALIDATION FAILED\n"
            f"{'='*70}\n"
            f"Expected: {expected_count} tests\n"
            f"Collected: {collected_count} tests\n"
            f"Difference: {collected_count - expected_count:+d} tests\n"
            f"\nTo update the expected count, edit pyproject.toml:\n"
            f"  [tool.cadence_netlist_format.testing]\n"
            f"  expected_test_count = {collected_count}\n"
            f"{'='*70}\n"
        )
        raise pytest.UsageError(msg)
