"""Run point"""

from __future__ import annotations

from .cadence_netlist_format import CadenceNetListFormat
from .commandlinearg import get_args


def main() -> None:
    """Run point for the application script"""
    get_args()
    CadenceNetListFormat().mainloop()
