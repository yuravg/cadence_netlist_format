"""
Unit tests for ConfigFile configuration management.

Tests config file creation, reading, key management, and persistence.
"""

import pytest
import tempfile
from pathlib import Path
from cadence_netlist_format.configfile import ConfigFile


@pytest.fixture
def sample_config_file(tmp_path):
    """Create a sample config file for testing."""
    config_file = tmp_path / "test_config.ini"
    content = """[Default]
name = test_value
path = /test/path

[Settings]
option1 = value1
option2 = value2
"""
    config_file.write_text(content)
    return str(config_file)


@pytest.fixture
def empty_config_file(tmp_path):
    """Create an empty config file path."""
    config_file = tmp_path / "empty_config.ini"
    return str(config_file)


@pytest.mark.unit
def test_configfile_creation_and_reading(sample_config_file):
    """Test config file creation and reading existing values."""
    # Create ConfigFile with empty initial keys
    config = ConfigFile(fname=sample_config_file, k={}, verbosity=0)

    # Verify file was read
    assert config.fname == sample_config_file

    # Verify sections and keys were loaded
    all_keys = config.get_all_keys()
    assert 'Default' in all_keys
    assert 'Settings' in all_keys

    # Verify key values
    assert config.get_key('Default', 'name') == 'test_value'
    assert config.get_key('Default', 'path') == '/test/path'
    assert config.get_key('Settings', 'option1') == 'value1'
    assert config.get_key('Settings', 'option2') == 'value2'


@pytest.mark.unit
def test_configfile_key_management(empty_config_file):
    """Test section and key management (add/get/set)."""
    # Create ConfigFile with initial keys
    initial_keys = {
        'Section1': {'key1': 'value1', 'key2': 'value2'},
        'Section2': {'keyA': 'valueA'}
    }
    config = ConfigFile(fname=empty_config_file, k=initial_keys, verbosity=0)

    # Verify initial keys are set
    assert config.get_key('Section1', 'key1') == 'value1'
    assert config.get_key('Section1', 'key2') == 'value2'
    assert config.get_key('Section2', 'keyA') == 'valueA'

    # Test edit_key (single key modification)
    config.edit_key('Section1', 'key1', 'modified_value1')
    assert config.get_key('Section1', 'key1') == 'modified_value1'

    # Test edit_key_dict (multiple keys modification)
    new_keys = {
        'Section1': {'key2': 'modified_value2', 'key3': 'new_value3'},
        'Section3': {'newKey': 'newValue'}
    }
    config.edit_key_dict(new_keys)

    # Verify modifications
    assert config.get_key('Section1', 'key2') == 'modified_value2'
    assert config.get_key('Section1', 'key3') == 'new_value3'
    assert config.get_key('Section3', 'newKey') == 'newValue'

    # Verify original keys still exist
    assert config.get_key('Section2', 'keyA') == 'valueA'


@pytest.mark.unit
def test_configfile_default_values_override(sample_config_file):
    """Test default values and config file override behavior."""
    # Create ConfigFile with default keys that will be overridden by file
    default_keys = {
        'Default': {'name': 'default_name', 'new_key': 'new_value'},
        'Settings': {'option1': 'default_option1'}
    }
    config = ConfigFile(fname=sample_config_file, k=default_keys, verbosity=0)

    # Verify file values override defaults
    assert config.get_key('Default', 'name') == 'test_value'  # from file, not 'default_name'
    assert config.get_key('Settings', 'option1') == 'value1'  # from file, not 'default_option1'

    # Verify default keys not in file are still present
    assert config.get_key('Default', 'new_key') == 'new_value'


@pytest.mark.unit
def test_configfile_persistence_write_reload(empty_config_file):
    """Test file persistence (write/reload cycle)."""
    # Create ConfigFile with initial keys
    initial_keys = {
        'Section1': {'key1': 'value1', 'key2': 'value2'},
        'Section2': {'keyA': 'valueA', 'keyB': 'valueB'}
    }
    config = ConfigFile(fname=empty_config_file, k=initial_keys, verbosity=0)

    # Modify some keys
    config.edit_key('Section1', 'key1', 'modified_value1')
    config.edit_key_dict({'Section2': {'keyC': 'valueC'}})

    # Write to file
    config.write2file()

    # Verify file was created
    assert Path(empty_config_file).exists()

    # Reload config from file
    reloaded_config = ConfigFile(fname=empty_config_file, k={}, verbosity=0)

    # Verify all keys persisted correctly
    assert reloaded_config.get_key('Section1', 'key1') == 'modified_value1'
    assert reloaded_config.get_key('Section1', 'key2') == 'value2'
    assert reloaded_config.get_key('Section2', 'keyA') == 'valueA'
    assert reloaded_config.get_key('Section2', 'keyB') == 'valueB'
    assert reloaded_config.get_key('Section2', 'keyC') == 'valueC'


@pytest.mark.unit
def test_configfile_missing_file_handling(tmp_path):
    """Test handling of missing/nonexistent config files."""
    nonexistent_file = str(tmp_path / "nonexistent.ini")

    # Create ConfigFile with nonexistent file (should not raise error)
    initial_keys = {
        'Default': {'key1': 'value1'}
    }
    config = ConfigFile(fname=nonexistent_file, k=initial_keys, verbosity=0)

    # Should still have initial keys
    assert config.get_key('Default', 'key1') == 'value1'

    # Should be able to write and create the file
    config.write2file()
    assert Path(nonexistent_file).exists()

    # Verify file can be read after creation
    reloaded_config = ConfigFile(fname=nonexistent_file, k={}, verbosity=0)
    assert reloaded_config.get_key('Default', 'key1') == 'value1'


@pytest.mark.unit
def test_configfile_get_all_keys(empty_config_file):
    """Test get_all_keys returns complete dictionary structure."""
    initial_keys = {
        'Section1': {'key1': 'value1', 'key2': 'value2'},
        'Section2': {'keyA': 'valueA'}
    }
    config = ConfigFile(fname=empty_config_file, k=initial_keys, verbosity=0)

    # Get all keys
    all_keys = config.get_all_keys()

    # Verify structure
    assert isinstance(all_keys, dict)
    assert 'Section1' in all_keys
    assert 'Section2' in all_keys

    # Verify nested structure
    assert all_keys['Section1']['key1'] == 'value1'
    assert all_keys['Section1']['key2'] == 'value2'
    assert all_keys['Section2']['keyA'] == 'valueA'


@pytest.mark.unit
def test_configfile_str_representation(empty_config_file):
    """Test string representation of ConfigFile."""
    initial_keys = {
        'Section1': {'key1': 'value1'},
        'Section2': {'keyA': 'valueA'}
    }
    config = ConfigFile(fname=empty_config_file, k=initial_keys, verbosity=0)

    # Convert to string
    config_str = str(config)

    # Verify string contains expected information
    assert empty_config_file in config_str
    assert 'Section1' in config_str
    assert 'Section2' in config_str
    assert 'key1' in config_str
    assert 'value1' in config_str
