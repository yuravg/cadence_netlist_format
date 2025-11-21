"""
Regression tests for Cadence netlist parsing.

Tests that the parser correctly handles the reference netlist files
(pstxnet_v1.dat, pstxnet_v2.dat, pstxnet_v3.dat) without errors.
"""

import pytest
import re
import tempfile
from pathlib import Path
from cadence_netlist_format.allegronetlist import AllegroNetList


# Test data paths
DATA_DIR = Path(__file__).parent.parent / "data"
NETLIST_V1 = DATA_DIR / "inputs" / "pstxnet_v1.dat"  # Big netlist (~1MB)
NETLIST_V2 = DATA_DIR / "inputs" / "pstxnet_v2.dat"  # Medium netlist (~2.4KB)
NETLIST_V3 = DATA_DIR / "inputs" / "pstxnet_v3.dat"  # Short netlist (~1.1KB)
REFERENCE_OUTPUT_V1 = DATA_DIR / "expected" / "netlist_v1_expected.rpt"  # Reference output for v1
REFERENCE_OUTPUT_V2 = DATA_DIR / "expected" / "netlist_v2_expected.rpt"  # Reference output for v2
REFERENCE_OUTPUT_V3 = DATA_DIR / "expected" / "netlist_v3_expected.rpt"  # Reference output for v3


def normalize_netlist_output(content):
    """Normalize netlist output for comparison.

    Replaces dynamic content (timestamps, file paths) with placeholders
    to enable reliable line-by-line comparison.

    Args:
        content (str): The netlist output content

    Returns:
        str: Normalized content with platform-independent line endings
    """
    # Normalize line endings (CRLF -> LF for cross-platform compatibility)
    content = content.replace('\r\n', '\n').replace('\r', '\n')

    # Normalize generation timestamp (line 3)
    # Example: "| generation date, time: 2016-12-06 12:13:42"
    content = re.sub(
        r'\| generation date, time: \d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}',
        '| generation date, time: YYYY-MM-DD HH:MM:SS',
        content
    )

    # Normalize file paths (line 7) - handles all path formats
    # Examples: "D:/HOME/.../file.dat", "./files/file.dat", "/home/.../file.dat", "file.dat"
    content = re.sub(
        r'\|  .*\.dat',  # Any .dat file path (Windows, Unix, relative, or bare filename)
        '|  <NORMALIZED_PATH>',
        content
    )

    return content


def compare_netlist_files(actual_path, expected_path):
    """Compare two netlist files line-by-line with normalization.

    Args:
        actual_path (Path): Path to actual output file
        expected_path (Path): Path to expected reference file

    Raises:
        AssertionError: If files don't match, with detailed diff information
    """
    # Read both files
    with open(actual_path, 'r', encoding='utf-8') as f:
        actual_content = f.read()

    with open(expected_path, 'r', encoding='utf-8') as f:
        expected_content = f.read()

    # Normalize both files
    actual_normalized = normalize_netlist_output(actual_content)
    expected_normalized = normalize_netlist_output(expected_content)

    # Split into lines for comparison
    actual_lines = actual_normalized.split('\n')
    expected_lines = expected_normalized.split('\n')

    # Compare line by line
    if actual_lines != expected_lines:
        # Find first difference for helpful error message
        max_lines = max(len(actual_lines), len(expected_lines))
        for i in range(max_lines):
            actual_line = actual_lines[i] if i < len(actual_lines) else '<EOF>'
            expected_line = expected_lines[i] if i < len(expected_lines) else '<EOF>'

            if actual_line != expected_line:
                raise AssertionError(
                    f"\nNetlist output differs from expected at line {i + 1}:\n"
                    f"  Expected: {expected_line!r}\n"
                    f"  Actual:   {actual_line!r}\n"
                    f"  (Total lines - Expected: {len(expected_lines)}, Actual: {len(actual_lines)})"
                )


@pytest.mark.regression
@pytest.mark.parametrize("netlist_path,reference_output_path,description", [
    pytest.param(
        NETLIST_V1, REFERENCE_OUTPUT_V1, "big netlist",
        marks=pytest.mark.slow,
        id="pstxnet_v1"
    ),
    pytest.param(
        NETLIST_V2, REFERENCE_OUTPUT_V2, "medium netlist",
        id="pstxnet_v2"
    ),
    pytest.param(
        NETLIST_V3, REFERENCE_OUTPUT_V3, "short netlist",
        id="pstxnet_v3"
    ),
])
def test_parse_netlist(netlist_path, reference_output_path, description):
    """Test parsing of reference netlists with output validation.

    Validates that:
    - File parses without errors
    - Produces non-empty net_list
    - Output matches expected reference file line-by-line
    - Version and date information is extracted

    Args:
        netlist_path: Path to the input netlist file
        reference_output_path: Path to the expected reference output file
        description: Description of the netlist (for documentation)
    """
    assert netlist_path.exists(), f"Test file not found: {netlist_path}"
    assert reference_output_path.exists(), f"Reference file not found: {reference_output_path}"

    # Parse the netlist
    netlist = AllegroNetList(str(netlist_path))

    # Validate basic properties
    assert netlist.net_list is not None, "net_list should not be None"
    assert netlist.net_list_length() > 0, "net_list should contain nets"

    # Validate version/date parsing
    assert netlist.version is not None, "version should be parsed"
    assert netlist.date is not None, "date should be parsed"
    assert netlist.time is not None, "time should be parsed"

    # Generate output and write to temporary file
    output = netlist.all_data2string()
    assert output is not None and len(output) > 0, "all_data2string() should produce output"

    # Write output to temporary file and compare with reference
    with tempfile.NamedTemporaryFile(mode='w', suffix='.rpt', delete=False, encoding='utf-8') as tmp_file:
        tmp_file.write(output)
        tmp_path = Path(tmp_file.name)

    try:
        # Compare actual output with expected reference file
        compare_netlist_files(tmp_path, reference_output_path)
    finally:
        # Clean up temporary file
        tmp_path.unlink()


@pytest.mark.regression
def test_all_netlists_have_consistent_structure():
    """Test that all reference netlists produce consistent data structures.

    Validates that all netlists:
    - Parse successfully
    - Have the expected data structure (list of [net_name, [[refdes, pin], ...]])
    - Have valid net names (strings)
    - Have valid node lists (lists)
    """
    netlists = [
        (NETLIST_V1, "pstxnet_v1.dat"),
        (NETLIST_V2, "pstxnet_v2.dat"),
        (NETLIST_V3, "pstxnet_v3.dat"),
    ]

    for netlist_path, name in netlists:
        if not netlist_path.exists():
            pytest.skip(f"Test file not found: {netlist_path}")

        netlist = AllegroNetList(str(netlist_path))

        # Validate structure
        assert isinstance(netlist.net_list, list), f"{name}: net_list should be a list"

        # Check first net structure (if exists)
        if len(netlist.net_list) > 0:
            first_net = netlist.net_list[0]
            assert isinstance(first_net, list), f"{name}: net entry should be a list"
            assert len(first_net) == 2, f"{name}: net entry should have 2 elements [name, nodes]"

            net_name, nodes = first_net
            assert isinstance(net_name, str), f"{name}: net name should be a string"
            assert isinstance(nodes, list), f"{name}: nodes should be a list"

            # Check node structure (if any nodes exist)
            if len(nodes) > 0:
                first_node = nodes[0]
                assert isinstance(first_node, list), f"{name}: node should be a list"
                assert len(first_node) >= 2, f"{name}: node should have at least [refdes, pin]"
