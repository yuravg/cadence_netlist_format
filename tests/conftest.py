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
