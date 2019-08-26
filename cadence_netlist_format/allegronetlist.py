#!/usr/bin/env python

# Time-stamp: <2018-02-19 14:55:01>
"""Get data from Cadence Allegro net-list
"""

from __future__ import print_function
import datetime

__version__ = '0.1.0'


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

    net_list = []
    date = 0
    time = 0
    version = 0
    refdes_list = []

    def __init__(self, fname):
        """Get data from net-list (read from file)
        """
        self.read_file(fname)
        self.fname = fname

    def read_file(self, fname):
        """read file data"""
        try:
            # print('read fname: ' + str(fname))
            with open(fname, 'r') as f:
                find_net_name = 0
                wait_end_net = 0
                net = []
                node = []
                cnt_string = 0
                wait_refdes_cnt = 0
                wait_refdes_en = False
                self.net_list = []
                for line in f:
                    s = line.rstrip()
                    try:
                        if find_net_name:
                            find_net_name = 0
                            wait_end_net = 1
                            # cut char - ' from net name
                            net = s[1:len(s)-1]
                            # print('Find net_name', net)
                        if s.find('NET_NAME') == 0 or s.find('END.') == 0:
                            if wait_end_net:
                                wait_end_net = 0
                                net_and_node = [net, node]
                                net = []
                                node = []
                                self.net_list.append(net_and_node)
                                # print('net and node:', net_and_node)
                            find_net_name = 1
                            net = s
                            # print('Wait net')
                        else:
                            if s.find('NODE_NAME') == 0:
                                s = s.split()
                                ref_des = s[1]
                                des_pin = s[2]
                                ref_and_pin = [ref_des, des_pin]
                                # print(' Find node:', ref_and_pin)
                                node.append(ref_and_pin)
                                wait_refdes_en = True
                                wait_refdes_cnt = 0
                        if wait_refdes_en:
                            if wait_refdes_cnt < 2:
                                wait_refdes_cnt = wait_refdes_cnt + 1
                            else:
                                wait_refdes_en = False
                                for char in "\ \';:":
                                    s = s.replace(char, '')
                                ref_and_pin.append(s)
                        if cnt_string < 3:
                            cnt_string = cnt_string + 1
                        if cnt_string == 2:
                            # NOTE: example sting:
                            #    { Using PSTWRITER 16.3.0 p002Mar-22-2016 at 10:54:51 }
                            cfg = s.split()
                            self.version = cfg[3]
                            self.date = cfg[4][4:]
                            self.time = cfg[6]
                    except OSError:
                        print('+-----------------------------------+')
                        print('| Error! With Net-list handler      |')
                        print('+-----------------------------------+')
            self.net_list.sort()
        except OSError:
            print('+-----------------------------------+')
            print('| Error! With file: \'%s\'' % fname)
            print('+-----------------------------------+')
        finally:
            f.close()

    def net_list_length(self):
        """Returns length of net-list"""
        return len(self.net_list)

    def check_net_index(self, i):
        """Check valid net-list index (to get net name)
        Keyword Arguments:
        i -- net-list index
        Returns:
        Returns true if index is valid
        """
        length = self.net_list_length()
        if i >= length:
            print('Error! Index of net=%d, more then net-list length=%d (from 0 to %d)' %
                  (i, length-1, length-1))
            return False
        else:
            return True

    def net_name(self, i):
        """Returns net name from net-list
        Keyword Arguments:
        i -- net name index
        Returns:
        Net name or false
        """
        if self.check_net_index(i):
            net = self.net_list[i][0]
            return net
        else:
            return False

    def node_list(self, i):
        """Returns refdes and pin list from net-list
        Keyword Arguments:
        i -- net name index
        """
        if self.check_net_index(i):
            node = []
            net = self.net_list[i][1]
            for i in net:
                v = i[:2]
                node.append(v)
            return node
        else:
            return 0

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
        node = ''
        node_list = self.node_list(i)
        for i in node_list:
            k = ' '.join(i)
            if node == '':
                node = '%s' % k
            else:
                node = '%s %s' % (node, k)
        return node

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
            print('Error! Can\'t find refdes: \'%s\' in net-list: %s' % (refdes, self.fname))
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
            print('Error! Can\'t find refdes: \'%s\'' % refdes)
            return ''

    def net2string(self, i):
        """Returns full net as sting (net name and her refdes and pins)
        Keyword Arguments:
        i -- net name index
        """
        net = self.net_name(i)
        node = self.node2string(i)
        # print('net: %s' % net)
        # print('node: %s' % node)
        net_and_node = '%s %s' % (net, node)
        # print('d: %s' % net_and_node)
        return net_and_node

    def __str__(self):
        """Returns net-list as sting
        """
        s = ''
        for i in range(self.net_list_length()):
            if s == '':
                s = '%s' % self.net2string(i)
            else:
                s = '%s\n%s' % (s, self.net2string(i))
        return s

    def net_list2string(self):
        """Return net-list data as stirng
        """
        s = ''
        for i in range(self.net_list_length()):
            string = self.net2string(i)
            s = s + string + '\n'
        return s

    def single_net_list2string(self):
        """Return single net-list data as stirng
        """
        s = ''
        for i in range(self.net_list_length()):
            string = self.net2string(i)
            length = len(string.split())
            if length < 5:
                s = s + string + '\n'
        return s

    def net_list_title(self):
        """Return net-list title as stirng
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
        """Write net-list data (with title to string) to file
        Keyword Arguments:
        fname -- output file name
        """
        s = self.all_data2string()
        f = open(fname, 'w')
        f.write(s)
        f.close()
        if message_en:
            print('Write Net-List report file: %s' % fname)

    def net_list_info(self):
        """Returns net-list info as string
        """
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
