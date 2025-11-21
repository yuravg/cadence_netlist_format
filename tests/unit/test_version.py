"""
Test package version information.

Tests that the package version is correctly exposed and matches pyproject.toml.
"""

import pytest
import toml
from pathlib import Path


@pytest.mark.unit
def test_package_version_exists():
    """Test that __version__ is defined in the package."""
    import cadence_netlist_format
    assert hasattr(cadence_netlist_format, '__version__')
    assert cadence_netlist_format.__version__ is not None


@pytest.mark.unit
def test_version_matches_pyproject():
    """Test that package version matches pyproject.toml."""
    import cadence_netlist_format

    # Load version from pyproject.toml
    project_root = Path(__file__).parent.parent.parent
    pyproject_path = project_root / "pyproject.toml"

    assert pyproject_path.exists(), "pyproject.toml not found"

    pyproject_data = toml.load(pyproject_path)
    expected_version = pyproject_data["project"]["version"]

    # Compare versions
    actual_version = cadence_netlist_format.__version__

    # Version might be "unknown" if not installed, so check for that case
    if actual_version != "unknown":
        assert actual_version == expected_version, \
            f"Version mismatch: package={actual_version}, pyproject.toml={expected_version}"


@pytest.mark.unit
def test_version_format():
    """Test that version follows semantic versioning format (X.Y.Z)."""
    import cadence_netlist_format
    import re

    version = cadence_netlist_format.__version__

    # Skip check if version is unknown (not installed)
    if version == "unknown":
        pytest.skip("Package not installed, version is 'unknown'")

    # Semantic versioning pattern: X.Y.Z or X.Y.Z-suffix
    version_pattern = r'^\d+\.\d+\.\d+(-[a-zA-Z0-9.]+)?$'
    assert re.match(version_pattern, version), \
        f"Version '{version}' does not follow semantic versioning (X.Y.Z)"
