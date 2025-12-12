#!/usr/bin/env python

"""Get data from Cadence Allegro Netlist
"""

from __future__ import annotations
import datetime
import logging
from pathlib import Path
from typing import Optional


# Configure module logger
logger = logging.getLogger(__name__)

# Translation table for cleaning pin names (performance optimization)
_PIN_NAME_TRANSLATE_TABLE = str.maketrans('', '', r"\ ';:")


class AllegroNetList:
    """Cadence Allegro Netlist data

    Attributes:
        date: Date of create Netlist
        time: Time of create Netlist
        version: Version of Cadence Allegro Netlist
        net_list: Netlist data [['net_name1', [['D1', '1'], ['C1', '1']]],
                                  ['net_name2', [['D2', '2'], ['R2', '2']]]]
        fname: Netlist file name
        refdes_list: List of pins and nets belong refdes
                     [['REFDES0',['net1', 'pin1'], ['net1', 'pin2'], ..., ['netN', 'pinN']],
                      ['REFDES1',['net1', 'pin1'], ['net1', 'pin2'], ..., ['netN', 'pinN']],
                      ['REFDESN',['net1', 'pin1'], ['net1', 'pin2'], ..., ['netN', 'pinN']]]
        refdes_dict: Performance index for O(1) refdes lookup
        pin_name_index: Performance index for O(1) (refdes, pin) -> pin_name lookup
    """

    def __init__(self, fname: str | Path) -> None:
        """Get data from Netlist (read from file)

        Args:
            fname: Path to the Netlist file
        """
        # Initialize instance attributes (not class attributes)
        self.net_list: list = []
        self.date: int | str = 0
        self.time: int | str = 0
        self.version: int | str = 0
        self.refdes_list: list = []
        self.refdes_dict: dict[str, int] = {}  # Performance: O(1) lookup for refdes
        self.pin_name_index: dict[tuple[str, str], str] = {}  # Performance: O(1) lookup for (refdes, pin) -> pin_name
        self.net_name_index: dict[tuple[str, str], str] = {}  # Performance: O(1) lookup for (refdes, pin) -> net_name
        self.fname: str = str(fname)
        self.read_file(fname)

    def read_file(self, fname: str | Path) -> None:
        """Read and parse Netlist data from file.

        The parser is a state machine that processes:
        1. Header lines (first 3 lines contain version/date/time)
        2. NET_NAME declarations (net name on next line)
        3. NODE_NAME entries (component + pin, with pin name 2 lines later)
        4. END marker (final Netlist termination)

        Args:
            fname: Path to Netlist file

        Raises:
            ValueError: If file size exceeds maximum allowed size (default: 100MB)
        """
        # Constants for clarity
        HEADER_LINE_COUNT = 3
        PIN_NAME_LINE_OFFSET = 2
        MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB limit to prevent DoS

        # Security: Check file size before reading to prevent memory exhaustion
        try:
            file_path = Path(fname)
            file_size = file_path.stat().st_size
            if file_size > MAX_FILE_SIZE:
                file_size_mb = file_size / (1024.0 * 1024.0)
                max_size_mb = MAX_FILE_SIZE / (1024.0 * 1024.0)
                error_msg = f'File size ({file_size_mb:.2f} MB) exceeds maximum allowed size ({max_size_mb:.2f} MB)'
                logger.error(error_msg)
                raise ValueError(error_msg)
            logger.info(f'File size: {file_size / (1024.0 * 1024.0):.2f} MB')
        except OSError as e:
            logger.error(f"Cannot check file size for '{fname}': {e}")
            raise

        try:
            with open(fname, 'r') as f:
                # State machine variables
                expecting_net_name = False  # Next line contains the net name
                processing_net = False      # Currently processing a net's nodes
                current_net = []
                current_nodes = []

                # Pin name extraction state
                waiting_for_pin_name = False
                pin_name_line_counter = 0
                current_node_ref = None  # Reference to node being processed

                # Header parsing
                header_line_number = 0

                # Error tracking
                parse_error_count = 0
                MAX_PARSE_ERRORS = 50  # Fail if more than 50 parsing errors occur

                self.net_list = []

                for line in f:
                    s = line.rstrip()

                    try:
                        # State 1: Extract net name (line after NET_NAME)
                        if expecting_net_name:
                            expecting_net_name = False
                            processing_net = True
                            # Remove surrounding single quotes from net name
                            current_net = s.strip("'")

                        # State 2: Process NET_NAME or END markers
                        if s.startswith('NET_NAME') or s.startswith('END.'):
                            # Save previous net if we were processing one
                            if processing_net:
                                processing_net = False
                                net_and_node = [current_net, current_nodes]
                                current_net = []
                                current_nodes = []
                                self.net_list.append(net_and_node)

                            # Reset pin name extraction state (fixes state machine bug)
                            waiting_for_pin_name = False
                            pin_name_line_counter = 0
                            current_node_ref = None

                            # Prepare for next net name
                            expecting_net_name = True
                            current_net = s

                        # State 3: Process NODE_NAME (component + pin)
                        elif s.startswith('NODE_NAME'):
                            parts = s.split()
                            ref_des = parts[1]
                            pin_number = parts[2]
                            ref_and_pin = [ref_des, pin_number]
                            current_nodes.append(ref_and_pin)

                            # Prepare to extract pin name (appears 2 lines later)
                            waiting_for_pin_name = True
                            pin_name_line_counter = 0
                            current_node_ref = ref_and_pin

                        # State 4: Extract pin name (2 lines after NODE_NAME)
                        if waiting_for_pin_name:
                            if pin_name_line_counter < PIN_NAME_LINE_OFFSET:
                                pin_name_line_counter += 1
                            else:
                                waiting_for_pin_name = False
                                # Clean up pin name (remove special characters) - optimized with str.translate()
                                pin_name = s.translate(_PIN_NAME_TRANSLATE_TABLE)
                                current_node_ref.append(pin_name)

                        # State 5: Parse header (first 3 lines contain metadata)
                        if header_line_number < HEADER_LINE_COUNT:
                            header_line_number += 1

                        if header_line_number == 2:
                            # Example header line 2:
                            #   { Using PSTWRITER 16.3.0 p002Mar-22-2016 at 10:54:51 }
                            cfg = s.split()
                            self.version = cfg[3]
                            self.date = cfg[4][4:]  # Remove "p002" prefix
                            self.time = cfg[6]

                    except (IndexError, KeyError) as e:
                        parse_error_count += 1
                        logger.warning(f'Error parsing Netlist data (error #{parse_error_count}): {e}')
                        # Check if too many errors have occurred
                        if parse_error_count >= MAX_PARSE_ERRORS:
                            error_msg = f'Too many parsing errors ({parse_error_count} errors). File may be corrupted or not a valid netlist.'
                            logger.error(error_msg)
                            raise ValueError(error_msg)

                # Parsing complete - report statistics
                if parse_error_count > 0:
                    logger.warning(f'Parsing completed with {parse_error_count} errors. Results may be incomplete.')

                # Sort nets alphabetically
                self.net_list.sort()

                # Validate header was properly parsed
                if header_line_number < HEADER_LINE_COUNT:
                    logger.warning('File appears to be incomplete or not a valid Cadence netlist (header incomplete)')
                if self.version == 0 or self.date == 0 or self.time == 0:
                    logger.warning('Could not parse version/date/time from header. File may not be a valid Cadence netlist.')

                # Build performance index: (refdes, pin) -> pin_name mapping
                for net in self.net_list:
                    node_list = net[1]
                    for node in node_list:
                        if len(node) >= 3:  # Ensure we have refdes, pin, and name
                            refdes, pin, name = node[0], node[1], node[2]
                            self.pin_name_index[(refdes, pin)] = name

                # Build performance index: (refdes, pin) -> net_name mapping (for O(1) lookup)
                for net in self.net_list:
                    net_name = net[0]
                    node_list = net[1]
                    for node in node_list:
                        if len(node) >= 2:  # Ensure we have refdes and pin
                            refdes, pin = node[0], node[1]
                            self.net_name_index[(refdes, pin)] = net_name

        except (IOError, OSError) as e:
            logger.error(f"Cannot read file '{fname}': {e}")
            raise

    def net_list_length(self) -> int:
        """Returns length of Netlist"""
        return len(self.net_list)

    def check_net_index(self, i: int) -> bool:
        """Check valid Netlist index (to get net name)

        Args:
            i: Netlist index

        Returns:
            True if index is valid, False otherwise

        Raises:
            TypeError: If i is not an integer
        """
        # Input validation: ensure i is an integer
        if not isinstance(i, int):
            raise TypeError(f'Index must be an integer, got {type(i).__name__}')

        length = self.net_list_length()
        if i < 0 or i >= length:
            logger.error(f'Invalid net index {i} (valid range: 0 to {length-1})')
            return False
        else:
            return True

    def net_name(self, i: int) -> Optional[str]:
        """Returns net name from Netlist

        Args:
            i: net name index

        Returns:
            Net name or None if index is invalid
        """
        if self.check_net_index(i):
            net = self.net_list[i][0]
            return net
        else:
            return None

    def node_list(self, i: int) -> Optional[list]:
        """Returns refdes and pin list from Netlist

        Args:
            i: net name index

        Returns:
            List of nodes or None if index is invalid
        """
        if self.check_net_index(i):
            node = []
            net = self.net_list[i][1]
            for node_entry in net:
                v = node_entry[:2]
                node.append(v)
            return node
        else:
            return None

    def get_refdes_pin_name(self, p_refdes: str, p_pin: str) -> Optional[str]:
        """Return refdes pin name as string

        Args:
            p_refdes: Reference designator (e.g., 'DD2')
            p_pin: Pin number (e.g., 'G3')

        Returns:
            Pin name if found, None otherwise

        Raises:
            TypeError: If p_refdes or p_pin is not a string

        Performance: O(1) lookup using pin_name_index dictionary
        """
        # Input validation
        if not isinstance(p_refdes, str):
            raise TypeError(f'p_refdes must be a string, got {type(p_refdes).__name__}')
        if not isinstance(p_pin, str):
            raise TypeError(f'p_pin must be a string, got {type(p_pin).__name__}')

        # Use O(1) dictionary lookup instead of nested loops
        return self.pin_name_index.get((p_refdes, p_pin), None)

    def node2string(self, i: int) -> Optional[str]:
        """Returns node (refdes, pin) as string

        Args:
            i: net name index

        Returns:
            Node string if valid index, None otherwise
        """
        node_list = self.node_list(i)
        if node_list is None:
            return None
        # Optimize: use join instead of string concatenation in loop
        node_strings = [' '.join(node_entry) for node_entry in node_list]
        return ' '.join(node_strings)

    def find_in_refdes_list(self, refdes: str) -> bool:
        """Find refdes in refdes list

        Args:
            refdes: refdes value

        Returns:
            True if refdes is found in refdes_list, False otherwise

        Performance: O(1) lookup using dictionary index
        """
        return refdes in self.refdes_dict

    def build_refdes_list(self, refdes: str) -> bool:
        """Build list of nets and pins belong of refdes - refdes list

        Args:
            refdes: refdes value

        Returns:
            True if refdes was found and added to refdes list,
            False if refdes was not found in Netlist
        """
        refdes_list = [refdes]
        find_net = 0
        if self.find_in_refdes_list(refdes):
            return True
        for i in self.net_list:
            net = i[0]
            ref_pin = i[1]
            for j in ref_pin:
                if j[0] == refdes:
                    refdes_list.append([net, j[1]])
                    find_net = 1
        # Add to both list and dictionary for O(1) lookup
        index = len(self.refdes_list)
        self.refdes_list.append(refdes_list)
        self.refdes_dict[refdes] = index
        if find_net:
            return True
        else:
            logger.error(f"Cannot find refdes '{refdes}' in Netlist: {self.fname}")
            return False

    def get_net_name4refdes_pin(self, refdes: str, pin: str) -> Optional[str]:
        """Returns net name for refdes and pin

        Args:
            refdes: refdes value
            pin: pin number

        Returns:
            Net name if found, None otherwise

        Performance: O(1) lookup using net_name_index dictionary
        """
        return self.net_name_index.get((refdes, pin), None)

    def refdes_list2string(self, refdes: str) -> Optional[str]:
        """Returns refdes_list (for selected refdes) as string

        Args:
            refdes: refdes value

        Returns:
            Refdes list as string if found, None otherwise
        """
        if self.find_in_refdes_list(refdes):
            s = ''
            for i in self.refdes_list:
                if i[0] == refdes:
                    s = f'{i[0]}'
                    net_pin = i[1:]
                    for j in net_pin:
                        s = f'{s} {j[0]}:{j[1]}'
            return s
        else:
            logger.error(f"Cannot find refdes '{refdes}' in refdes list")
            return None

    def net2string(self, i: int) -> Optional[str]:
        """Returns full net as string (net name and her refdes and pins)

        Args:
            i: net name index

        Returns:
            Net as string if valid index, None otherwise
        """
        net = self.net_name(i)
        if net is None:
            return None
        node = self.node2string(i)
        if node is None:
            return None
        net_and_node = f'{net} {node}'
        return net_and_node

    def __str__(self) -> str:
        """Returns Netlist as string"""
        # Optimize: use join instead of string concatenation in loop, filter out None values
        lines = [self.net2string(i) for i in range(self.net_list_length())]
        lines = [line for line in lines if line is not None]
        return '\n'.join(lines)

    def net_list2string(self) -> str:
        """Return Netlist data as string"""
        # Optimize: use join instead of string concatenation in loop, filter out None values
        lines = [self.net2string(i) for i in range(self.net_list_length())]
        lines = [line for line in lines if line is not None]
        return '\n'.join(lines) + '\n'

    def single_net_list2string(self) -> str:
        """Return single Netlist data as string"""
        # Optimize: use join with list comprehension, filter out None values
        lines = []
        for i in range(self.net_list_length()):
            net_str = self.net2string(i)
            if net_str is not None and len(net_str.split()) < 5:
                lines.append(net_str)
        return '\n'.join(lines) + '\n' if lines else ''

    def net_list_title(self) -> str:
        """Return Netlist title as string"""
        date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # Optimize: use list and join instead of string concatenation
        lines = [
            '+-------------------------------------------------------------------------+',
            '| File contains Cadence PCB Editor netlist                                |',
            '| NOTE: this file was auto-generated                                      |',
            f'| generation date, time: {date}                              |',
            '+-------------------------------------------------------------------------+',
            '| Cadence Netlist file info:                                             |',
            f'|  {self.net_list_info()}',
            f'|  {self.fname}',
            '+-------------------------------------------------------------------------+'
        ]
        return '\n'.join(lines)

    def single_net_warnings(self) -> str:
        """Return single net warning as string"""
        # Optimize: use list and join instead of string concatenation
        lines = [
            '',
            '',
            '',
            '+-------------------------------------------------------------------------+',
            '| Warnings: Single node name                                              |',
            '+-------------------------------------------------------------------------+'
        ]
        w_string = self.single_net_list2string()
        if w_string == '':
            lines.append('- (Empty)')
        else:
            lines.append(w_string)
        return '\n'.join(lines)

    def all_data2string(self) -> str:
        """Return all Netlist data (title, data, warnings) as string"""
        s = self.net_list_title() + '\n'
        s = s + self.net_list2string()
        s = s + self.single_net_warnings()
        # Add trailing newline (Unix convention)
        return s + '\n'

    def net_list2file(self, fname: str | Path = 'NetList.rpt', message_en: bool = False) -> None:
        """Write Netlist data (with title to string) to file

        Args:
            fname: output file name
            message_en: if True, log a message about the write operation

        Raises:
            IOError: If file write fails (permission denied, disk full, etc.)
        """
        try:
            s = self.all_data2string()
            with open(fname, 'w') as f:
                f.write(s)
            if message_en:
                logger.info(f'Wrote Netlist report file: {fname}')
        except (IOError, OSError) as e:
            error_msg = f"Failed to write output file '{fname}': {e}"
            logger.error(error_msg)
            raise IOError(error_msg)

    def net_list_info(self) -> str:
        """Returns Netlist info as string"""
        return f'Netlist {self.date} {self.time} (version: {self.version})'


if __name__ == '__main__':
    # Module can be tested directly, but tests should use the test suite in tests/
    import sys
    if len(sys.argv) < 2:
        print('Usage: python -m cadence_netlist_format.allegronetlist <netlist_file>')
        print('Example: python -m cadence_netlist_format.allegronetlist tests/data/inputs/pstxnet_v3.dat')
        sys.exit(1)

    fname = sys.argv[1]
    print(f'Parsing netlist file: {fname}')
    try:
        netlist = AllegroNetList(fname)
        print(f'\nNetlist info: {netlist.net_list_info()}')
        print(f'Total nets: {netlist.net_list_length()}')
        print('\nFirst 5 nets:')
        for i in range(min(5, netlist.net_list_length())):
            print(f'  {netlist.net2string(i)}')
    except Exception as e:
        print(f'ERROR: {e}')
        sys.exit(1)
