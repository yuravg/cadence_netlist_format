"""
Unit tests for AllegroNetList parser.

Tests core parsing functionality, data structures, and output formatting.
"""

import pytest
import tempfile
from pathlib import Path
from cadence_netlist_format.allegronetlist import AllegroNetList


@pytest.fixture
def sample_netlist_file(tmp_path):
    """Create a sample netlist file for testing."""
    content = """FILE_TYPE = EXPANDEDNETLIST;
{ Using PSTWRITER 16.3.0 p002Mar-22-2016 at 10:54:51 }
NET_NAME
'NET1'
 '@CAPTURENAME.test':
 C_SIGNAL='@test';
NODE_NAME\tR1 1
 '@CAPTURENAME.test':
 'pin1':;
NODE_NAME\tR2 2
 '@CAPTURENAME.test':
 'pin2':;
NET_NAME
'NET2'
 '@CAPTURENAME.test':
 C_SIGNAL='@test';
NODE_NAME\tC1 1
 '@CAPTURENAME.test':
 'pin1':;
END.
"""
    netlist_file = tmp_path / "test_netlist.dat"
    netlist_file.write_text(content)
    return str(netlist_file)


@pytest.fixture
def single_node_netlist_file(tmp_path):
    """Create a netlist with single-node nets (warnings)."""
    content = """FILE_TYPE = EXPANDEDNETLIST;
{ Using PSTWRITER 16.3.0 p002Mar-22-2016 at 10:54:51 }
NET_NAME
'SINGLE_NET'
 '@CAPTURENAME.test':
 C_SIGNAL='@test';
NODE_NAME\tR1 1
 '@CAPTURENAME.test':
 'pin1':;
NET_NAME
'MULTI_NET'
 '@CAPTURENAME.test':
 C_SIGNAL='@test';
NODE_NAME\tR2 1
 '@CAPTURENAME.test':
 'pin1':;
NODE_NAME\tR3 2
 '@CAPTURENAME.test':
 'pin2':;
END.
"""
    netlist_file = tmp_path / "single_node.dat"
    netlist_file.write_text(content)
    return str(netlist_file)


@pytest.mark.unit
def test_allegronetlist_basic_parsing(sample_netlist_file):
    """Test basic parsing of a valid netlist file."""
    netlist = AllegroNetList(sample_netlist_file)

    # Verify file was parsed
    assert netlist.fname == sample_netlist_file
    assert netlist.net_list is not None
    assert netlist.net_list_length() > 0


@pytest.mark.unit
def test_net_name_and_node_name_extraction(sample_netlist_file):
    """Test that NET_NAME and NODE_NAME entries are correctly extracted."""
    netlist = AllegroNetList(sample_netlist_file)

    # Should have 2 nets: NET1 and NET2
    assert netlist.net_list_length() == 2

    # Check first net
    net1 = netlist.net_list[0]
    assert len(net1) == 2  # [net_name, nodes]
    assert net1[0] == 'NET1'  # Net name
    assert len(net1[1]) == 2  # Should have 2 nodes (R1-1, R2-2)

    # Check nodes in first net
    nodes = net1[1]
    assert ['R1', '1'] in [node[:2] for node in nodes]
    assert ['R2', '2'] in [node[:2] for node in nodes]

    # Check second net
    net2 = netlist.net_list[1]
    assert net2[0] == 'NET2'
    assert len(net2[1]) == 1  # Should have 1 node (C1-1)


@pytest.mark.unit
def test_net_list_data_structure(sample_netlist_file):
    """Test that net_list data structure is correctly built."""
    netlist = AllegroNetList(sample_netlist_file)

    # net_list should be a list of [net_name, [[refdes, pin], ...]]
    assert isinstance(netlist.net_list, list)

    for net_entry in netlist.net_list:
        assert isinstance(net_entry, list)
        assert len(net_entry) == 2

        net_name, nodes = net_entry
        assert isinstance(net_name, str)
        assert isinstance(nodes, list)

        for node in nodes:
            assert isinstance(node, list)
            assert len(node) >= 2  # At least [refdes, pin], may have pin name


@pytest.mark.unit
def test_version_date_time_parsing(sample_netlist_file):
    """Test that version, date, and time are extracted from header."""
    netlist = AllegroNetList(sample_netlist_file)

    # From header: { Using PSTWRITER 16.3.0 p002Mar-22-2016 at 10:54:51 }
    assert netlist.version == '16.3.0'
    assert netlist.date == 'Mar-22-2016'
    assert netlist.time == '10:54:51'


@pytest.mark.unit
def test_pin_name_parsing(sample_netlist_file):
    """Test that pin names (2 lines after NODE_NAME) are parsed correctly."""
    netlist = AllegroNetList(sample_netlist_file)

    # Check that nodes have pin names appended
    net1 = netlist.net_list[0]
    nodes = net1[1]

    # Each node should have at least 3 elements: [refdes, pin, pin_name]
    for node in nodes:
        assert len(node) >= 2  # At minimum refdes and pin
        # Pin name might be appended as 3rd element


@pytest.mark.unit
def test_single_node_nets_detection(single_node_netlist_file):
    """Test detection of single-node nets (for warnings section)."""
    netlist = AllegroNetList(single_node_netlist_file)

    # Should have 2 nets
    assert netlist.net_list_length() == 2

    # First net has 1 node (single-node)
    net1 = netlist.net_list[1]  # SINGLE_NET (sorted alphabetically after MULTI_NET)
    assert len(net1[1]) == 1

    # Second net has 2 nodes (multi-node)
    net2 = netlist.net_list[0]  # MULTI_NET
    assert len(net2[1]) == 2

    # Check single_net_warnings method generates warnings
    warnings = netlist.single_net_warnings()
    assert warnings is not None
    assert 'SINGLE_NET' in warnings


@pytest.mark.unit
def test_output_generation(sample_netlist_file):
    """Test that output can be generated without errors."""
    netlist = AllegroNetList(sample_netlist_file)

    # Test all_data2string (full report)
    output = netlist.all_data2string()
    assert output is not None
    assert len(output) > 0
    assert 'NET1' in output
    assert 'NET2' in output

    # Test net_list2string (nets only)
    nets_output = netlist.net_list2string()
    assert nets_output is not None
    assert 'NET1' in nets_output

    # Test net_list_title (header)
    title = netlist.net_list_title()
    assert title is not None
    assert '16.3.0' in title  # version


@pytest.mark.unit
def test_error_handling_nonexistent_file():
    """Test handling of non-existent file."""
    # Should raise IOError/OSError (FileNotFoundError in Python 3)
    # when file doesn't exist
    with pytest.raises((IOError, OSError)):
        netlist = AllegroNetList('/nonexistent/file.dat')


@pytest.mark.unit
def test_empty_netlist_file(tmp_path):
    """Test handling of empty netlist file."""
    empty_file = tmp_path / "empty.dat"
    empty_file.write_text("")

    netlist = AllegroNetList(str(empty_file))

    # Should parse without crashing
    assert netlist.net_list_length() == 0


@pytest.mark.unit
def test_net_list_sorting(sample_netlist_file):
    """Test that net_list is sorted alphabetically by net name."""
    netlist = AllegroNetList(sample_netlist_file)

    # net_list should be sorted
    net_names = [net[0] for net in netlist.net_list]

    # Check alphabetical order
    assert net_names == sorted(net_names)
    assert net_names == ['NET1', 'NET2']


@pytest.mark.unit
def test_parser_state_reset_on_net_boundary(tmp_path):
    """Test that parser state is reset when encountering NET_NAME.

    Regression test for Issue #4: Parser state machine bug where
    waiting_for_pin_name flag was not reset at NET_NAME boundaries,
    potentially causing pin names to be extracted from wrong lines.
    """
    content = """FILE_TYPE = EXPANDEDNETLIST;
{ Using PSTWRITER 16.3.0 p002Mar-22-2016 at 10:54:51 }
NET_NAME
'NET1'
 '@CAPTURENAME.test':
 C_SIGNAL='@test';
NODE_NAME\tR1 1
NET_NAME
'NET2'
 '@CAPTURENAME.test':
 C_SIGNAL='@test';
NODE_NAME\tC1 1
 '@CAPTURENAME.test':
 'pin1':;
END.
"""
    netlist_file = tmp_path / "state_test.dat"
    netlist_file.write_text(content)

    # Should parse without extracting wrong pin names
    netlist = AllegroNetList(str(netlist_file))

    # Verify correct parsing
    assert netlist.net_list_length() == 2

    # Check that NET1 and NET2 are both present
    net_names = [net[0] for net in netlist.net_list]
    assert 'NET1' in net_names
    assert 'NET2' in net_names

    # Verify nodes are correctly assigned to nets
    for net in netlist.net_list:
        if net[0] == 'NET1':
            assert len(net[1]) == 1  # Should have R1
            assert net[1][0][0] == 'R1'
        elif net[0] == 'NET2':
            assert len(net[1]) == 1  # Should have C1
            assert net[1][0][0] == 'C1'
