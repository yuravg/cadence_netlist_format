#!/usr/bin/env python

"""Format Cadence Allegro Net-List file (cnl - Cadence Let-List) to readable view
"""

import os
import datetime
try:
    from tkinter import Frame, Label, Button, StringVar
    from tkinter.filedialog import askopenfilename
except ImportError:  # for version < 3.0
    from Tkinter import Frame, Label, Button, StringVar
    from tkFileDialog import askopenfilename
from .configfile import ConfigFile
from .allegronetlist import AllegroNetList


class CadenceNetListFormat(Frame):
    """Format Cadence Allegro net-list file (cnl - Cadence net-list) to human readable view
    """

    def __init__(self, parent=None):
        Frame.__init__(self, parent)
        self.cnl_fname = None
        self.read_config_file()
        self.master.title("Cadence Allegro net-list format")
        self.master.geometry("500x230")
        self.pack()
        self.make_widgets()

    def read_config_file(self):
        """reading configuration file"""
        k = {'Configuration': {'netlist_file': ''},
             'Info': {'Description': 'Configuration file to Format Cadence Allegro net-list file'}}
        self.cfg = ConfigFile('.cnl_format.dat', k)
        self.cnl_fname = self.cfg.get_key('Configuration', 'netlist_file')

    def save_config(self):
        """save setting to configuration file"""
        self.cfg.edit_key('Configuration', 'netlist_file', self.cnl_fname)
        self.cfg.write2file()

    def make_widgets(self):
        """making main widgets"""
        Label(self, text='Cadence net-list:').pack()
        fname = self.cnl_fname
        self.gui_cnl_fname = StringVar()
        self.gui_cnl_fname.set(fname)
        Label(self, textvariable=self.gui_cnl_fname).pack()
        Button(self, text='Browse', command=self.select_netlist, height=1, width=10).pack()

        Label(self, text='').pack()
        Button(self, text='Build', command=self.build, height=1, width=10).pack()
        self.state = StringVar()
        self.state.set('Idle')
        Label(self, textvariable=self.state).pack()
        Label(self, text='').pack()
        Button(self, text='Exit', command=self.save_and_exit, height=1, width=10).pack()

    def update_gui2self(self):
        """update from GUI to self data"""
        self.cnl_fname = self.gui_cnl_fname.get()

    def update_self2gui(self):
        """update form self data to GUI"""
        self.gui_cnl_fname.set(self.cnl_fname)

    def update_and_save_config(self):
        """update data and save config"""
        self.update_gui2self()
        self.save_config()

    def build(self):
        """build formatted net-list"""
        self.update_and_save_config()
        self.state.set('Runnig...')
        n = AllegroNetList(self.cnl_fname)
        fname = 'NetList.rpt'
        s = n.all_data2string()
        self.write2newfile(fname, s)
        data = datetime.datetime.strftime(datetime.datetime.now(), '%H:%M:%S')
        work_dir = os.getcwd()
        done_msg = 'Done: %s\nwrited file: %s\n(output directory: %s)' % (data, fname, work_dir)
        self.state.set(done_msg)

    def select_netlist(self):
        """GUI to select net-list"""
        fname = askopenfilename(filetypes=(("Cadence neltist", "pstxnet.dat"),
                                           ("All files", "*.*")))
        if fname != '':
            self.cnl_fname = fname
            self.update_self2gui()

    def save_and_exit(self):
        """save configuration data and exit
        """
        self.update_and_save_config()
        self.quit()

    def write2newfile(self, fname, s):
        """write data to file
        if file not exist new file will created
        if file exist it will renamed and new file will created"""
        if os.path.exists(fname):
            for i in range(100):
                new_fname = '%s,%s' % (fname, i)
                if not os.path.exists(new_fname):
                    os.rename(fname, new_fname)
                    print('renamed old file to %s' % new_fname)
                    break
        self.write2file(fname, s)

    def write2file(self, fname, s):
        """write data to file"""
        f = open(fname, 'w')
        f.write(s)
        f.close()


if __name__ == '__main__':
    CadenceNetListFormat().mainloop()
