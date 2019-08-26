"""Run point"""

from .cadence_netlist_format import CadenceNetListFormat
from .commandlinearg import get_args


def main():
    """Run point for the application script"""
    get_args()
    CadenceNetListFormat().mainloop()
