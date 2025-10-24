"""Cadence Netlist Format CLI application package."""

try:
    from importlib.metadata import version, PackageNotFoundError
    __version__ = version("cadence_netlist_format")
except (ImportError, PackageNotFoundError):
    __version__ = "unknown"

# Define public interface
__all__ = ["__version__"]
