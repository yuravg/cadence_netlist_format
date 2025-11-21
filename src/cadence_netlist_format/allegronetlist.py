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
        """
        # Constants for clarity
        HEADER_LINE_COUNT = 3
        PIN_NAME_LINE_OFFSET = 2

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
                        logger.warning('Error parsing net-list data: %s', str(e))

                # Sort nets alphabetically
                self.net_list.sort()

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
        """
        length = self.net_list_length()
        if i >= length:
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
        """Return refdes pin name as string"""
        # print(self.net_list)
        for net in self.net_list:
            # print('net: %s' % net)
            node_list = net[1]
            # print('node_list: %s' % node_list)
            for node in node_list:
                # print('node: %s' % node)
                refdes = node[0]
                pin = node[1]
                name = node[2]
                if refdes == p_refdes:
                    if pin == p_pin:
                        return name
        return ""

    def node2string(self, i):
        """Returns node (refdes, pin) as string
        Keyword Arguments:
        i -- net name index
        """
        node_list = self.node_list(i)
        if node_list is None:
            return ''
        # Optimize: use join instead of string concatenation in loop
        node_strings = [' '.join(node_entry) for node_entry in node_list]
        return ' '.join(node_strings)

    def find_in_refdes_list(self, refdes):
        """Find refdes in refdes list
        Keyword Arguments:
        refdes -- refdes value
        Returns:
        Returns true if find refdes in refdes_netlist
        """
        for i in self.refdes_list:
            if i[0] == refdes:
                return True
        return False

    def build_refdes_list(self, refdes):
        """Build list of nets and pins belong of refdes - refdes list
        Keyword Arguments:
        refdes -- refdes value
        Returns:
        Returns true if find refdes and just added it to refdes list,
        or false in there are not refdes in net-list
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
        self.refdes_list.append(refdes_list)
        if find_net:
            return True
        else:
            logger.error('Cannot find refdes \'%s\' in net-list: %s', refdes, self.fname)
            return False

    def get_net_name4refdes_pin(self, refdes, pin):
        """Returns net name for refdes and pin
        Keyword Arguments:
        refdes -- refdes value
        pin    -- pin number
        Returns:
        Net name or '' (empty string) if there are not net for selected refdes and pin
        """
        for i in self.refdes_list:
            if i[0] == refdes:
                net_pin = i[1:]
                for j in net_pin:
                    if j[1] == pin:
                        return j[0]
        return ''

    def refdes_list2string(self, refdes):
        """Returns refdes_list (for selected refdes) as string
        Keyword Arguments:
        refdes -- refdes value
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
            return ''

    def net2string(self, i):
        """Returns full net as string (net name and her refdes and pins)
        Keyword Arguments:
        i -- net name index
        """
        net = self.net_name(i)
        if net is None:
            return ''
        node = self.node2string(i)
        # print('net: %s' % net)
        # print('node: %s' % node)
        net_and_node = '%s %s' % (net, node)
        # print('d: %s' % net_and_node)
        return net_and_node

    def __str__(self):
        """Returns net-list as string
        """
        # Optimize: use join instead of string concatenation in loop
        lines = [self.net2string(i) for i in range(self.net_list_length())]
        return '\n'.join(lines)

    def net_list2string(self):
        """Return net-list data as string
        """
        # Optimize: use join instead of string concatenation in loop
        lines = [self.net2string(i) for i in range(self.net_list_length())]
        return '\n'.join(lines) + '\n'

    def single_net_list2string(self):
        """Return single net-list data as string
        """
        # Optimize: use join with list comprehension (avoid calling net2string twice)
        lines = []
        for i in range(self.net_list_length()):
            net_str = self.net2string(i)
            if len(net_str.split()) < 5:
                lines.append(net_str)
        return '\n'.join(lines) + '\n' if lines else ''

    def net_list_title(self):
        """Return net-list title as string
        """
        date = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d %H:%M:%S')
        s = ''
        s = s + '+-------------------------------------------------------------------------+\n'
        s = s + '| File contains Cadence PCB Editor netlist                                |\n'
        s = s + '| NOTE: this file was auto-generated                                      |\n'
        s = s + '| generation date, time: %s                              |\n' % date
        s = s + '+-------------------------------------------------------------------------+\n'
        s = s + '| Cadence net-list file info:                                             |\n'
        s = s + '|  %s\n' % (self.net_list_info())
        s = s + '|  %s\n' % (self.fname)
        s = s + '+-------------------------------------------------------------------------+'
        return s

    def single_net_warnings(self):
        """Return single net warning as string
        """
        s = '\n'*3
        s = s + '+-------------------------------------------------------------------------+\n'
        s = s + '| Warnings: Single node name                                              |\n'
        s = s + '+-------------------------------------------------------------------------+\n'
        w_string = self.single_net_list2string()
        if w_string == '':
            s = s + '- (Empty)'
        else:
            s = s + w_string
        return s

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
        """
        s = self.all_data2string()
        with open(fname, 'w') as f:
            f.write(s)
        if message_en:
            logger.info('Wrote Net-List report file: %s', fname)

    def net_list_info(self):
        # type: () -> str
        """Returns net-list info as string"""
        return 'Net-list %s %s (version: %s)' % (self.date, self.time, self.version)


if __name__ == '__main__':
    print('____________________________________________')
    fname1 = '../test/pstxnet_simple1.dat'
    fname1rpt = '../test/NetList_simple1.rpt'
    netlist1 = AllegroNetList(fname1)
    netlist1.net_list2file(fname1rpt, True)

    fname2 = '../test/pstxnet_simple2.dat.dat'
    fname2rpt = '../test/NetList_simple2.rpt'
    netlist2 = AllegroNetList(fname2)
    netlist2.net_list2file(fname2rpt, True)

    print('')
    print(netlist1.net_list_info())
    print('Net-list data (begin):')
    print(netlist1)
    print('Net-list data (end).')
    print('')
    print('')
    print('Run: Build net list')
    netlist1.build_refdes_list('DD2')
    netlist1.build_refdes_list('DA153')
    RD = 'DD2'
    PIN = 'G3'
    print('Get net name by refdes(%s) and pin(%s): %s(net name)' %
          (RD, PIN, netlist1.get_net_name4refdes_pin(RD, PIN)))
    print('')
    print('refdes_list = %s' % netlist1.refdes_list)
    print('')
    RD = 'DD2'
    print('Search in refdes_list \'%s\', result: %s' % (RD, netlist1.find_in_refdes_list(RD)))
    print('')
    print('Refdes to string: %s' % netlist1.refdes_list2string('DD2'))
    print(datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d %H:%M:%S'))
    print('*****')
    print('Check net name:')
    print('node_n-DIFFIO_L1N ?= %s' % netlist1.get_refdes_pin_name('DD2', 'G3'))
    print('node_n-VCCIO1_D4  ?= %s' % netlist1.get_refdes_pin_name('DD2', 'D4'))
