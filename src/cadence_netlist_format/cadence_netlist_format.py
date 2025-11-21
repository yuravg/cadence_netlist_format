#!/usr/bin/env python

"""Format Cadence Allegro Net-List file (cnl - Cadence Let-List) to readable view
"""

import os
import sys
import datetime
import subprocess
try:
    from tkinter import Frame, Label, Button, StringVar, Entry, Text, Scrollbar
    from tkinter import messagebox, END, DISABLED, NORMAL, WORD
    from tkinter.ttk import Separator, Style
    from tkinter.filedialog import askopenfilename
except ImportError:  # for version < 3.0
    from Tkinter import Frame, Label, Button, StringVar, Entry, Text, Scrollbar
    from Tkinter import END, DISABLED, NORMAL, WORD
    import tkMessageBox as messagebox
    from tkFileDialog import askopenfilename
from .configfile import ConfigFile
from .allegronetlist import AllegroNetList


class CadenceNetListFormat(Frame):
    """Format Cadence Allegro net-list file (cnl - Cadence net-list) to human readable view
    """

    def __init__(self, parent=None):
        Frame.__init__(self, parent)
        self.cnl_fname = None
        self.output_fname = 'NetList.rpt'
        self.read_config_file()
        self.master.title("Cadence Allegro Net-List Formatter")
        self.master.geometry("700x500")
        self.master.minsize(600, 400)
        self.pack(fill='both', expand=True, padx=10, pady=10)
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
        # Input file section
        input_frame = Frame(self)
        input_frame.pack(fill='x', pady=(0, 10))

        Label(input_frame, text='Input Netlist File:', font=('TkDefaultFont', 9, 'bold')).pack(anchor='w')

        file_entry_frame = Frame(input_frame)
        file_entry_frame.pack(fill='x', pady=5)

        self.gui_cnl_fname = StringVar()
        self.gui_cnl_fname.set(self.cnl_fname if self.cnl_fname else '')

        self.file_entry = Entry(file_entry_frame, textvariable=self.gui_cnl_fname, state='readonly')
        self.file_entry.pack(side='left', fill='x', expand=True, padx=(0, 5))

        Button(file_entry_frame, text='Browse...', command=self.select_netlist,
               width=12).pack(side='left')

        # Action buttons section
        action_frame = Frame(self)
        action_frame.pack(fill='x', pady=10)

        Button(action_frame, text='Format Netlist', command=self.format_netlist,
               height=2, width=15, bg='#4CAF50', fg='white',
               font=('TkDefaultFont', 9, 'bold')).pack(side='left', padx=5)

        Button(action_frame, text='Open Output File', command=self.open_output_file,
               height=2, width=15).pack(side='left', padx=5)

        Button(action_frame, text='Open Output Folder', command=self.open_output_dir,
               height=2, width=15).pack(side='left', padx=5)

        # Status and log section
        status_frame = Frame(self)
        status_frame.pack(fill='both', expand=True, pady=10)

        Label(status_frame, text='Status Log:', font=('TkDefaultFont', 9, 'bold')).pack(anchor='w')

        # Text widget with scrollbar
        text_frame = Frame(status_frame)
        text_frame.pack(fill='both', expand=True, pady=5)

        scrollbar = Scrollbar(text_frame)
        scrollbar.pack(side='right', fill='y')

        self.log_text = Text(text_frame, height=10, wrap=WORD,
                            yscrollcommand=scrollbar.set, state=DISABLED)
        self.log_text.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.log_text.yview)

        # Bottom buttons
        bottom_frame = Frame(self)
        bottom_frame.pack(fill='x', pady=(10, 0))

        Button(bottom_frame, text='Clear Log', command=self.clear_log,
               width=12).pack(side='left', padx=5)

        Button(bottom_frame, text='Exit', command=self.save_and_exit,
               width=12).pack(side='right', padx=5)

        # Initial log message
        self.log_message('Ready. Please select a netlist file to begin.')

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

    def format_netlist(self):
        """format netlist into readable report"""
        # Validate input file
        if not self.cnl_fname or self.cnl_fname == '':
            messagebox.showerror("Error", "Please select a netlist file first.")
            self.log_message('ERROR: No netlist file selected.')
            return

        if not os.path.exists(self.cnl_fname):
            messagebox.showerror("Error", f"File not found:\n{self.cnl_fname}")
            self.log_message(f'ERROR: File not found: {self.cnl_fname}')
            return

        self.update_and_save_config()

        try:
            self.log_message('=' * 60)
            self.log_message(f'Starting format at {datetime.datetime.now().strftime("%H:%M:%S")}')
            self.log_message(f'Input file: {self.cnl_fname}')

            # Parse netlist
            self.log_message('Parsing netlist file...')
            n = AllegroNetList(self.cnl_fname)

            # Generate report
            self.log_message('Generating formatted report...')
            s = n.all_data2string()

            # Write output
            fname = self.output_fname
            self.write2newfile(fname, s)

            work_dir = os.getcwd()
            output_path = os.path.join(work_dir, fname)

            self.log_message(f'SUCCESS: Report written to: {output_path}')
            self.log_message(f'Completed at {datetime.datetime.now().strftime("%H:%M:%S")}')
            self.log_message('=' * 60)

        except Exception as e:
            error_msg = f'ERROR: Failed to format netlist: {str(e)}'
            self.log_message(error_msg)
            self.log_message('=' * 60)
            messagebox.showerror("Format Failed", f"An error occurred:\n\n{str(e)}")

    def select_netlist(self):
        """GUI to select net-list"""
        fname = askopenfilename(filetypes=(("Cadence netlist", "pstxnet.dat"),
                                           ("All files", "*.*")))
        if fname != '':
            self.cnl_fname = fname
            self.update_self2gui()
            self.log_message(f'Selected input file: {fname}')

    def save_and_exit(self):
        """save configuration data and exit
        """
        self.update_and_save_config()
        self.quit()

    def log_message(self, message):
        """Add message to log text widget"""
        self.log_text.config(state=NORMAL)
        self.log_text.insert(END, message + '\n')
        self.log_text.see(END)  # Auto-scroll to bottom
        self.log_text.config(state=DISABLED)
        self.update_idletasks()  # Update GUI immediately

    def clear_log(self):
        """Clear the log text widget"""
        self.log_text.config(state=NORMAL)
        self.log_text.delete(1.0, END)
        self.log_text.config(state=DISABLED)
        self.log_message('Log cleared.')

    def _open_with_system_app(self, path):
        """Open a file or directory with the system's default application.

        Args:
            path: Path to file or directory to open

        Raises:
            Exception: If opening fails
        """
        if sys.platform == 'win32':
            os.startfile(path)
        elif sys.platform == 'darwin':  # macOS
            subprocess.call(['open', path])
        else:  # linux
            subprocess.call(['xdg-open', path])

    def open_output_file(self):
        """Open the output report file"""
        output_path = os.path.join(os.getcwd(), self.output_fname)

        if not os.path.exists(output_path):
            messagebox.showwarning("File Not Found",
                                 f"Output file does not exist yet:\n{output_path}\n\nPlease format the netlist first.")
            self.log_message(f'Cannot open output file - file does not exist: {output_path}')
            return

        try:
            self._open_with_system_app(output_path)
            self.log_message(f'Opened output file: {output_path}')
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open file:\n{str(e)}")
            self.log_message(f'ERROR: Failed to open output file: {str(e)}')

    def open_output_dir(self):
        """Open the output directory in file manager"""
        work_dir = os.getcwd()

        try:
            self._open_with_system_app(work_dir)
            self.log_message(f'Opened output directory: {work_dir}')
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open directory:\n{str(e)}")
            self.log_message(f'ERROR: Failed to open directory: {str(e)}')

    def write2newfile(self, fname, s):
        """write data to file
        if file not exist new file will created
        if file exist it will renamed and new file will created"""
        if os.path.exists(fname):
            for i in range(100):
                new_fname = '%s,%s' % (fname, i)
                if not os.path.exists(new_fname):
                    os.rename(fname, new_fname)
                    self.log_message(f'Renamed old file to: {new_fname}')
                    break
        self.write2file(fname, s)

    def write2file(self, fname, s):
        """write data to file"""
        with open(fname, 'w') as f:
            f.write(s)


if __name__ == '__main__':
    CadenceNetListFormat().mainloop()
