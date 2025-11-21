#!/usr/bin/env python

"""Get data from Cadence Allegro net-list
"""

from __future__ import print_function
import datetime
import logging

__version__ = '1.0'

# Configure module logger
logger = logging.getLogger(__name__)


class AllegroNetList(object):
    """Cadence Allegro net-list data

    Arguments:
    date/time -- date/time of create net-list
    version   -- version of Cadence Allegro net-list
    net_list  -- net-list data
                    [['net_name1', [['D1', '1'], ['C1', '1']]],
                     ['net_name2', [['D2', '2'], ['R2', '2']]]]
    fname     -- net-list file name
    refdes_list -- list of pins and nets belong refdes
                (to build list need run method: build_refdes_list(REFDES)
                    [['REFDES0',['net1', 'pin1'], ['net1', 'pin2'], ..., ['netN', 'pinN']],
                     ['REFDES1',['net1', 'pin1'], ['net1', 'pin2'], ..., ['netN', 'pinN']],
                     ['REFDESN',['net1', 'pin1'], ['net1', 'pin2'], ..., ['netN', 'pinN']]]
    """

    def __init__(self, fname):
        # type: (str) -> None
        """Get data from net-list (read from file)

        Args:
            fname: Path to the netlist file
        """
        # Initialize instance attributes (not class attributes)
        self.net_list = []  # type: list
        self.date = 0  # type: int
        self.time = 0  # type: int
        self.version = 0  # type: int
        self.refdes_list = []  # type: list
        self.refdes_dict = {}  # type: dict - Performance: O(1) lookup for refdes
        self.pin_name_index = {}  # type: dict - Performance: O(1) lookup for (refdes, pin) -> pin_name
        self.fname = fname  # type: str
        self.read_file(fname)

    def read_file(self, fname):
        # type: (str) -> None
        """Read and parse netlist data from file.

        The parser is a state machine that processes:
        1. Header lines (first 3 lines contain version/date/time)
        2. NET_NAME declarations (net name on next line)
        3. NODE_NAME entries (component + pin, with pin name 2 lines later)
        4. END marker (final net-list termination)

        Args:
            fname: Path to netlist file

        Raises:
            ValueError: If file size exceeds maximum allowed size (default: 100MB)
        """
        # Constants for clarity
        HEADER_LINE_COUNT = 3
        PIN_NAME_LINE_OFFSET = 2
        MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB limit to prevent DoS

        # Security: Check file size before reading to prevent memory exhaustion
        try:
            import os
            file_size = os.path.getsize(fname)
            if file_size > MAX_FILE_SIZE:
                error_msg = 'File size ({:.2f} MB) exceeds maximum allowed size ({:.2f} MB)'.format(
                    file_size / (1024.0 * 1024.0),
                    MAX_FILE_SIZE / (1024.0 * 1024.0)
                )
                logger.error(error_msg)
                raise ValueError(error_msg)
            logger.info('File size: {:.2f} MB'.format(file_size / (1024.0 * 1024.0)))
        except OSError as e:
            logger.error('Cannot check file size for \'%s\': %s', fname, str(e))
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
                                # Clean up pin name (remove special characters)
                                pin_name = s
                                for char in r"\ ';:":
                                    pin_name = pin_name.replace(char, '')
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
                        logger.warning('Error parsing net-list data (error #%d): %s', parse_error_count, str(e))
                        # Check if too many errors have occurred
                        if parse_error_count >= MAX_PARSE_ERRORS:
                            error_msg = 'Too many parsing errors ({} errors). File may be corrupted or not a valid netlist.'.format(parse_error_count)
                            logger.error(error_msg)
                            raise ValueError(error_msg)

                # Parsing complete - report statistics
                if parse_error_count > 0:
                    logger.warning('Parsing completed with %d errors. Results may be incomplete.', parse_error_count)

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

        except (IOError, OSError) as e:
            logger.error('Cannot read file \'%s\': %s', fname, str(e))
            raise

    def net_list_length(self):
        # type: () -> int
        """Returns length of net-list"""
        return len(self.net_list)

    def check_net_index(self, i):
        # type: (int) -> bool
        """Check valid net-list index (to get net name)

        Args:
            i: net-list index

        Returns:
            True if index is valid, False otherwise

        Raises:
            TypeError: If i is not an integer
        """
        # Input validation: ensure i is an integer
        if not isinstance(i, int):
            raise TypeError('Index must be an integer, got {}'.format(type(i).__name__))

        length = self.net_list_length()
        if i < 0 or i >= length:
            logger.error('Invalid net index %d (valid range: 0 to %d)', i, length-1)
            return False
        else:
            return True

    def net_name(self, i):
        # type: (int) -> str
        """Returns net name from net-list

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

    def node_list(self, i):
        """Returns refdes and pin list from net-list
        Keyword Arguments:
        i -- net name index
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

    def get_refdes_pin_name(self, p_refdes, p_pin):
        """Return refdes pin name as string

        Args:
            p_refdes: Reference designator (e.g., 'DD2')
            p_pin: Pin number (e.g., 'G3')

        Returns:
            str: Pin name if found, None otherwise

        Raises:
            TypeError: If p_refdes or p_pin is not a string

        Performance: O(1) lookup using pin_name_index dictionary
        """
        # Input validation
        if not isinstance(p_refdes, str):
            raise TypeError('p_refdes must be a string, got {}'.format(type(p_refdes).__name__))
        if not isinstance(p_pin, str):
            raise TypeError('p_pin must be a string, got {}'.format(type(p_pin).__name__))

        # Use O(1) dictionary lookup instead of nested loops
        return self.pin_name_index.get((p_refdes, p_pin), None)

    def node2string(self, i):
        """Returns node (refdes, pin) as string

        Args:
            i: net name index

        Returns:
            str: Node string if valid index, None otherwise
        """
        node_list = self.node_list(i)
        if node_list is None:
            return None
        # Optimize: use join instead of string concatenation in loop
        node_strings = [' '.join(node_entry) for node_entry in node_list]
        return ' '.join(node_strings)

    def find_in_refdes_list(self, refdes):
        """Find refdes in refdes list

        Args:
            refdes: refdes value

        Returns:
            bool: True if refdes is found in refdes_list, False otherwise

        Performance: O(1) lookup using dictionary index
        """
        return refdes in self.refdes_dict

    def build_refdes_list(self, refdes):
        """Build list of nets and pins belong of refdes - refdes list

        Args:
            refdes: refdes value

        Returns:
            bool: True if refdes was found and added to refdes list,
                  False if refdes was not found in net-list
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
            logger.error('Cannot find refdes \'%s\' in net-list: %s', refdes, self.fname)
            return False

    def get_net_name4refdes_pin(self, refdes, pin):
        """Returns net name for refdes and pin

        Args:
            refdes: refdes value
            pin: pin number

        Returns:
            str: Net name if found, None otherwise
        """
        for i in self.refdes_list:
            if i[0] == refdes:
                net_pin = i[1:]
                for j in net_pin:
                    if j[1] == pin:
                        return j[0]
        return None

    def refdes_list2string(self, refdes):
        """Returns refdes_list (for selected refdes) as string

        Args:
            refdes: refdes value

        Returns:
            str: Refdes list as string if found, None otherwise
        """
        if self.find_in_refdes_list(refdes):
            s = ''
            for i in self.refdes_list:
                if i[0] == refdes:
                    s = '%s' % i[0]
                    net_pin = i[1:]
                    for j in net_pin:
                        s = '%s %s:%s' % (s, j[0], j[1])
            return s
        else:
            logger.error('Cannot find refdes \'%s\' in refdes list', refdes)
            return None

    def net2string(self, i):
        """Returns full net as string (net name and her refdes and pins)

        Args:
            i: net name index

        Returns:
            str: Net as string if valid index, None otherwise
        """
        net = self.net_name(i)
        if net is None:
            return None
        node = self.node2string(i)
        if node is None:
            return None
        net_and_node = '%s %s' % (net, node)
        return net_and_node

    def __str__(self):
        """Returns net-list as string
        """
        # Optimize: use join instead of string concatenation in loop, filter out None values
        lines = [self.net2string(i) for i in range(self.net_list_length())]
        lines = [line for line in lines if line is not None]
        return '\n'.join(lines)

    def net_list2string(self):
        """Return net-list data as string
        """
        # Optimize: use join instead of string concatenation in loop, filter out None values
        lines = [self.net2string(i) for i in range(self.net_list_length())]
        lines = [line for line in lines if line is not None]
        return '\n'.join(lines) + '\n'

    def single_net_list2string(self):
        """Return single net-list data as string
        """
        # Optimize: use join with list comprehension, filter out None values
        lines = []
        for i in range(self.net_list_length()):
            net_str = self.net2string(i)
            if net_str is not None and len(net_str.split()) < 5:
                lines.append(net_str)
        return '\n'.join(lines) + '\n' if lines else ''

    def net_list_title(self):
        """Return net-list title as string
        """
        date = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d %H:%M:%S')
        # Optimize: use list and join instead of string concatenation
        lines = [
            '+-------------------------------------------------------------------------+',
            '| File contains Cadence PCB Editor netlist                                |',
            '| NOTE: this file was auto-generated                                      |',
            '| generation date, time: %s                              |' % date,
            '+-------------------------------------------------------------------------+',
            '| Cadence net-list file info:                                             |',
            '|  %s' % (self.net_list_info()),
            '|  %s' % (self.fname),
            '+-------------------------------------------------------------------------+'
        ]
        return '\n'.join(lines)

    def single_net_warnings(self):
        """Return single net warning as string
        """
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

    def all_data2string(self):
        """Return all net-list data (tilte, data, warnings) as string
        """
        s = self.net_list_title() + '\n'
        s = s + self.net_list2string()
        s = s + self.single_net_warnings()
        return s

    def net_list2file(self, fname='NetList.rpt', message_en=False):
        # type: (str, bool) -> None
        """Write net-list data (with title to string) to file

        Args:
            fname: output file name
            message_en: if True, log a message about the write operation

        Raises:
            IOError/OSError: If file write fails (permission denied, disk full, etc.)
        """
        try:
            s = self.all_data2string()
            with open(fname, 'w') as f:
                f.write(s)
            if message_en:
                logger.info('Wrote Net-List report file: %s', fname)
        except (IOError, OSError) as e:
            error_msg = 'Failed to write output file \'{}\': {}'.format(fname, str(e))
            logger.error(error_msg)
            raise IOError(error_msg)

    def net_list_info(self):
        # type: () -> str
        """Returns net-list info as string"""
        return 'Net-list %s %s (version: %s)' % (self.date, self.time, self.version)


if __name__ == '__main__':
    # Module can be tested directly, but tests should use the test suite in tests/
    import sys
    if len(sys.argv) < 2:
        print('Usage: python -m cadence_netlist_format.allegronetlist <netlist_file>')
        print('Example: python -m cadence_netlist_format.allegronetlist tests/data/inputs/pstxnet_v3.dat')
        sys.exit(1)

    fname = sys.argv[1]
    print('Parsing netlist file: {}'.format(fname))
    try:
        netlist = AllegroNetList(fname)
        print('\nNetlist info: {}'.format(netlist.net_list_info()))
        print('Total nets: {}'.format(netlist.net_list_length()))
        print('\nFirst 5 nets:')
        for i in range(min(5, netlist.net_list_length())):
            print('  {}'.format(netlist.net2string(i)))
    except Exception as e:
        print('ERROR: {}'.format(str(e)))
        sys.exit(1)
