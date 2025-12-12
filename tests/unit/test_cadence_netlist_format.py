"""
Unit tests for CadenceNetListFormat GUI application.

Tests config file handling, file validation, output generation,
error handling, and cross-platform compatibility.

Note: GUI components (tkinter Frame, widgets) are mocked to avoid X11/display requirements.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call, mock_open
from cadence_netlist_format.cadence_netlist_format import CadenceNetListFormat


# Helper function to create GUI instance without actual tkinter initialization
def create_test_app(monkeypatch=None):
    """Create a CadenceNetListFormat instance with mocked GUI components."""
    # Mock tkinter components to avoid X11 display requirements
    with patch('tkinter.Frame.__init__', return_value=None):
        app = CadenceNetListFormat.__new__(CadenceNetListFormat)

        # Initialize attributes that would normally be set by Frame and __init__
        app.master = Mock()
        app.master.title = Mock()
        app.master.geometry = Mock()
        app.master.minsize = Mock()
        app.cnl_fname = None
        app.output_fname = 'NetList.rpt'
        app.cfg = None
        app.log_text = Mock()  # Mock text widget
        app.gui_cnl_fname = Mock()  # Mock StringVar
        app.file_entry = Mock()

        # Mock methods that interact with GUI
        app.pack = Mock()
        app.update_idletasks = Mock()
        app.update_self2gui = Mock()
        app.update_gui2self = Mock()
        app.log_message = Mock()

        return app


@pytest.fixture
def sample_netlist(tmp_path):
    """Create a minimal valid netlist file for testing."""
    content = """FILE_TYPE = EXPANDEDNETLIST;
{ Using PSTWRITER 16.3.0 p002Mar-22-2016 at 10:54:51 }
NET_NAME
'TEST_NET'
 '@CAPTURENAME.test':
 C_SIGNAL='@test';
NODE_NAME\tR1 1
 '@CAPTURENAME.test':
 'pin1':;
NODE_NAME\tR2 2
 '@CAPTURENAME.test':
 'pin2':;
END.
"""
    netlist_file = tmp_path / "test_netlist.dat"
    netlist_file.write_text(content)
    return netlist_file


@pytest.fixture
def invalid_netlist(tmp_path):
    """Create an invalid netlist file (missing FILE_TYPE header)."""
    content = """This is not a valid Cadence netlist file.
Just some random text.
"""
    invalid_file = tmp_path / "invalid.dat"
    invalid_file.write_text(content)
    return invalid_file


@pytest.fixture
def valid_config_file(tmp_path):
    """Create a valid config file for testing."""
    config_file = tmp_path / ".cnl_format.dat"
    content = """[Configuration]
netlist_file = /test/path/netlist.dat

[Info]
description = Configuration file to Format Cadence Allegro Netlist file
"""
    config_file.write_text(content)
    return config_file


# ============================================================================
# Config File Handling Tests
# ============================================================================

@pytest.mark.unit
def test_read_config_file_valid(valid_config_file, monkeypatch):
    """Test read_config_file with valid config."""
    monkeypatch.chdir(valid_config_file.parent)
    app = create_test_app()
    app.read_config_file()

    # Verify config was loaded
    assert app.cfg is not None
    assert app.cnl_fname == '/test/path/netlist.dat'


@pytest.mark.unit
def test_read_config_file_missing(tmp_path, monkeypatch):
    """Test read_config_file with missing config (fallback to defaults)."""
    monkeypatch.chdir(tmp_path)
    app = create_test_app()
    app.read_config_file()

    # Should fallback to empty filename
    assert app.cnl_fname == ''


@pytest.mark.unit
def test_read_config_file_corrupted(tmp_path, monkeypatch, capsys):
    """Test read_config_file with corrupted config (should handle gracefully)."""
    # Create corrupted config file
    config_file = tmp_path / ".cnl_format.dat"
    config_file.write_text("This is not valid INI format\ncorrupted data")

    monkeypatch.chdir(tmp_path)
    app = create_test_app()
    app.read_config_file()

    # Should handle error and fallback to defaults
    assert app.cnl_fname == ''


@pytest.mark.unit
def test_save_config_successful(tmp_path, monkeypatch):
    """Test save_config writes correctly."""
    monkeypatch.chdir(tmp_path)

    app = create_test_app()
    app.read_config_file()  # Initialize cfg
    app.cnl_fname = '/new/test/path.dat'
    app.save_config()

    # Verify config file was created
    config_file = tmp_path / ".cnl_format.dat"
    assert config_file.exists()


@pytest.mark.unit
def test_save_config_when_cfg_is_none(tmp_path, monkeypatch):
    """Test save_config when cfg is None (should handle gracefully)."""
    monkeypatch.chdir(tmp_path)

    app = create_test_app()
    app.cfg = None  # Simulate failed config load
    app.save_config()  # Should return silently without error


# ============================================================================
# File Validation Tests
# ============================================================================

@pytest.mark.unit
def test_format_netlist_no_file_selected(tmp_path, monkeypatch):
    """Test format_netlist with no file selected (should show error)."""
    monkeypatch.chdir(tmp_path)

    with patch('cadence_netlist_format.cadence_netlist_format.messagebox') as mock_msgbox:
        app = create_test_app()
        app.cnl_fname = ''  # No file selected
        app.format_netlist()

        # Verify error was shown
        mock_msgbox.showerror.assert_called_once()
        assert 'select' in mock_msgbox.showerror.call_args[0][1].lower()


@pytest.mark.unit
def test_format_netlist_nonexistent_file(tmp_path, monkeypatch):
    """Test format_netlist with non-existent file."""
    monkeypatch.chdir(tmp_path)

    with patch('cadence_netlist_format.cadence_netlist_format.messagebox') as mock_msgbox:
        app = create_test_app()
        app.cnl_fname = str(tmp_path / "nonexistent.dat")
        app.format_netlist()

        # Verify error was shown
        mock_msgbox.showerror.assert_called_once()
        assert 'not found' in mock_msgbox.showerror.call_args[0][1].lower()


@pytest.mark.unit
def test_format_netlist_directory_instead_of_file(tmp_path, monkeypatch):
    """Test format_netlist with directory instead of file."""
    monkeypatch.chdir(tmp_path)
    test_dir = tmp_path / "testdir"
    test_dir.mkdir()

    with patch('cadence_netlist_format.cadence_netlist_format.messagebox') as mock_msgbox:
        app = create_test_app()
        app.cnl_fname = str(test_dir)
        app.format_netlist()

        # Verify error was shown
        mock_msgbox.showerror.assert_called_once()
        assert 'directory' in mock_msgbox.showerror.call_args[0][1].lower()


@pytest.mark.unit
def test_format_netlist_invalid_cadence_file(invalid_netlist, tmp_path, monkeypatch):
    """Test format_netlist with invalid Cadence file (missing FILE_TYPE header)."""
    monkeypatch.chdir(tmp_path)

    app = create_test_app()
    app.cnl_fname = str(invalid_netlist)
    app.update_and_save_config = Mock()
    app.format_netlist()

    # Verify warning was logged
    log_calls = [str(call) for call in app.log_message.call_args_list]
    warning_logged = any('WARNING' in str(call) and 'FILE_TYPE' in str(call)
                        for call in log_calls)
    assert warning_logged


# ============================================================================
# Output Generation Tests
# ============================================================================

@pytest.mark.unit
def test_format_netlist_successful(sample_netlist, tmp_path, monkeypatch):
    """Test format_netlist with valid netlist file."""
    monkeypatch.chdir(tmp_path)

    app = create_test_app()
    app.cnl_fname = str(sample_netlist)
    app.update_and_save_config = Mock()
    app.format_netlist()

    # Verify output file was created
    output_file = tmp_path / "NetList.rpt"
    assert output_file.exists()

    # Verify success was logged
    log_calls = [str(call) for call in app.log_message.call_args_list]
    success_logged = any('SUCCESS' in str(call) for call in log_calls)
    assert success_logged


@pytest.mark.unit
def test_write2newfile_creates_backup_versions(tmp_path, monkeypatch):
    """Test write2newfile creates backup versions (,01, ,02, etc.)."""
    monkeypatch.chdir(tmp_path)

    app = create_test_app()

    # Create initial file
    test_file = tmp_path / "test.rpt"
    app.write2newfile(test_file, "version 1")
    assert test_file.read_text() == "version 1"

    # Write again - should create backup
    app.write2newfile(test_file, "version 2")
    assert test_file.read_text() == "version 2"
    backup1 = tmp_path / "test.rpt,01"
    assert backup1.exists()
    assert backup1.read_text() == "version 1"

    # Write third time - should create second backup
    app.write2newfile(test_file, "version 3")
    assert test_file.read_text() == "version 3"
    backup2 = tmp_path / "test.rpt,02"
    assert backup2.exists()
    assert backup2.read_text() == "version 2"


@pytest.mark.unit
def test_write2newfile_backup_limit_99_files(tmp_path, monkeypatch):
    """Test that write2newfile enforces 99 backup limit."""
    monkeypatch.chdir(tmp_path)

    app = create_test_app()
    test_file = tmp_path / "test.rpt"

    # Create 99 backup files
    for i in range(1, 100):
        backup = tmp_path / f"test.rpt,{i:02d}"
        backup.write_text(f"backup {i}")

    # Initial file
    test_file.write_text("current")

    # Try to write when 99 backups exist - should raise error
    with pytest.raises(IOError, match="Too many backup files"):
        app.write2newfile(test_file, "new content")


@pytest.mark.unit
def test_write2newfile_atomic_write_pattern(tmp_path, monkeypatch):
    """Test write2newfile atomic write pattern (temp file → rename)."""
    monkeypatch.chdir(tmp_path)

    app = create_test_app()
    test_file = tmp_path / "test.rpt"

    # Write file
    app.write2newfile(test_file, "test content")

    # Verify no temp files left behind
    temp_files = list(tmp_path.glob("*.tmp"))
    assert len(temp_files) == 0

    # Verify final file exists with correct content
    assert test_file.exists()
    assert test_file.read_text() == "test content"


# ============================================================================
# Error Handling Tests
# ============================================================================

@pytest.mark.unit
def test_format_netlist_ioerror_handling(sample_netlist, tmp_path, monkeypatch):
    """Test IOError handling during netlist parsing."""
    monkeypatch.chdir(tmp_path)

    with patch('cadence_netlist_format.cadence_netlist_format.AllegroNetList') as mock_netlist:
        with patch('cadence_netlist_format.cadence_netlist_format.messagebox') as mock_msgbox:
            # Simulate IOError during parsing
            mock_netlist.side_effect = IOError("Disk read error")

            app = create_test_app()
            app.cnl_fname = str(sample_netlist)
            app.update_and_save_config = Mock()
            app.format_netlist()

            # Verify error was shown to user
            mock_msgbox.showerror.assert_called_once()
            assert 'File Error' in mock_msgbox.showerror.call_args[0][0]


@pytest.mark.unit
def test_format_netlist_valueerror_handling(sample_netlist, tmp_path, monkeypatch):
    """Test ValueError handling for invalid file format."""
    monkeypatch.chdir(tmp_path)

    with patch('cadence_netlist_format.cadence_netlist_format.AllegroNetList') as mock_netlist:
        with patch('cadence_netlist_format.cadence_netlist_format.messagebox') as mock_msgbox:
            # Simulate ValueError during parsing
            mock_netlist.side_effect = ValueError("Invalid format")

            app = create_test_app()
            app.cnl_fname = str(sample_netlist)
            app.update_and_save_config = Mock()
            app.format_netlist()

            # Verify error was shown to user
            mock_msgbox.showerror.assert_called_once()
            assert 'Format Error' in mock_msgbox.showerror.call_args[0][0]


# ============================================================================
# Cross-Platform Compatibility Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.skipif(sys.platform != 'win32', reason="os.startfile only exists on Windows")
def test_open_with_system_app_windows(tmp_path):
    """Test _open_with_system_app on Windows (conditional test)."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("test")

    with patch('os.startfile') as mock_startfile:
        app = create_test_app()
        app._open_with_system_app(test_file)

        # Verify os.startfile was called
        mock_startfile.assert_called_once_with(str(test_file))


@pytest.mark.unit
def test_open_with_system_app_macos(tmp_path, monkeypatch):
    """Test _open_with_system_app on macOS."""
    monkeypatch.setattr(sys, 'platform', 'darwin')

    test_file = tmp_path / "test.txt"
    test_file.write_text("test")

    with patch('subprocess.Popen') as mock_popen:
        app = create_test_app()
        app._open_with_system_app(test_file)

        # Verify subprocess.Popen was called with 'open'
        mock_popen.assert_called_once()
        call_args = mock_popen.call_args[0][0]
        assert call_args[0] == 'open'
        assert str(test_file) in call_args


@pytest.mark.unit
def test_open_with_system_app_linux(tmp_path, monkeypatch):
    """Test _open_with_system_app on Linux."""
    monkeypatch.setattr(sys, 'platform', 'linux')

    test_file = tmp_path / "test.txt"
    test_file.write_text("test")

    with patch('subprocess.Popen') as mock_popen:
        app = create_test_app()
        app._open_with_system_app(test_file)

        # Verify subprocess.Popen was called with 'xdg-open'
        mock_popen.assert_called_once()
        call_args = mock_popen.call_args[0][0]
        assert call_args[0] == 'xdg-open'
        assert str(test_file) in call_args


@pytest.mark.unit
def test_open_with_system_app_error_handling(tmp_path, monkeypatch):
    """Test _open_with_system_app error handling."""
    monkeypatch.setattr(sys, 'platform', 'linux')

    test_file = tmp_path / "test.txt"
    test_file.write_text("test")

    with patch('subprocess.Popen', side_effect=OSError("Command not found")):
        app = create_test_app()

        # Should raise OSError with helpful message
        with pytest.raises(OSError, match="Failed to open with system application"):
            app._open_with_system_app(test_file)


@pytest.mark.unit
def test_open_output_file_not_exists(tmp_path, monkeypatch):
    """Test open_output_file when file doesn't exist."""
    monkeypatch.chdir(tmp_path)

    with patch('cadence_netlist_format.cadence_netlist_format.messagebox') as mock_msgbox:
        app = create_test_app()
        app.output_fname = "NonExistent.rpt"
        app.open_output_file()

        # Verify warning was shown
        mock_msgbox.showwarning.assert_called_once()
        assert 'does not exist' in mock_msgbox.showwarning.call_args[0][1].lower()


@pytest.mark.unit
def test_open_output_dir(tmp_path, monkeypatch):
    """Test open_output_dir opens current directory."""
    monkeypatch.chdir(tmp_path)

    with patch.object(CadenceNetListFormat, '_open_with_system_app') as mock_open:
        app = create_test_app()
        app.open_output_dir()

        # Verify _open_with_system_app was called with working directory
        mock_open.assert_called_once()
        assert str(tmp_path) in str(mock_open.call_args)
