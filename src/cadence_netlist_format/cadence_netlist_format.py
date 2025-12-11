#!/usr/bin/env python

"""Format Cadence Allegro Netlist file (cnl - Cadence Netlist) to readable view
"""

from __future__ import annotations
import datetime
import subprocess
import sys
from pathlib import Path
from tkinter import Frame, Label, Button, StringVar, Entry, Text, Scrollbar
from tkinter import messagebox, END, DISABLED, NORMAL, WORD
from tkinter.filedialog import askopenfilename
from typing import Optional

from .configfile import ConfigFile
from .allegronetlist import AllegroNetList


class CadenceNetListFormat(Frame):
    """Format Cadence Allegro Netlist file (cnl - Cadence Netlist) to human readable view"""

    def __init__(self, parent=None) -> None:
        Frame.__init__(self, parent)
        self.cnl_fname: Optional[str] = None
        self.output_fname: str = 'NetList.rpt'
        self.cfg: Optional[ConfigFile] = None
        self.read_config_file()
        self.master.title("Cadence Allegro Netlist Formatter")
        self.master.geometry("700x500")
        self.master.minsize(600, 400)
        self.pack(fill='both', expand=True, padx=10, pady=10)
        self.make_widgets()

    def read_config_file(self) -> None:
        """Read configuration file with error handling and fallback to defaults"""
        k = {'Configuration': {'netlist_file': ''},
             'Info': {'Description': 'Configuration file to Format Cadence Allegro Netlist file'}}
        try:
            self.cfg = ConfigFile('.cnl_format.dat', k)
            self.cnl_fname = self.cfg.get_key('Configuration', 'netlist_file')
        except (IOError, OSError, KeyError) as e:
            # Config file is corrupted or unreadable - fall back to defaults
            print(f'Warning: Cannot read config file, using defaults: {e}')
            self.cfg = None
            self.cnl_fname = ''

    def save_config(self) -> None:
        """Save settings to configuration file"""
        if self.cfg is None:
            # Config was not loaded successfully, skip saving
            return
        try:
            self.cfg.edit_key('Configuration', 'netlist_file', self.cnl_fname)
            self.cfg.write2file()
        except (IOError, OSError) as e:
            # Silently fail if we can't save config - not critical
            print(f'Warning: Failed to save config file: {e}')

    def make_widgets(self) -> None:
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
        self.log_message('Ready. Please select a Netlist file to begin.')

    def update_gui2self(self) -> None:
        """update from GUI to self data"""
        self.cnl_fname = self.gui_cnl_fname.get()

    def update_self2gui(self) -> None:
        """update form self data to GUI"""
        self.gui_cnl_fname.set(self.cnl_fname)

    def update_and_save_config(self) -> None:
        """update data and save config"""
        self.update_gui2self()
        self.save_config()

    def format_netlist(self) -> None:
        """format Netlist into readable report"""
        # Validate input file
        if not self.cnl_fname or self.cnl_fname == '':
            messagebox.showerror("Error", "Please select a Netlist file first.")
            self.log_message('ERROR: No Netlist file selected.')
            return

        file_path = Path(self.cnl_fname)

        if not file_path.exists():
            messagebox.showerror("Error", f"File not found:\n{self.cnl_fname}")
            self.log_message(f'ERROR: File not found: {self.cnl_fname}')
            return

        # Additional validation: check if it's a directory
        if file_path.is_dir():
            messagebox.showerror("Error", f"Path is a directory, not a file:\n{self.cnl_fname}")
            self.log_message(f'ERROR: Path is a directory: {self.cnl_fname}')
            return

        # Check if file is readable
        if not file_path.is_file():
            messagebox.showerror("Error", f"Path is not a regular file:\n{self.cnl_fname}")
            self.log_message(f'ERROR: Path is not a regular file: {self.cnl_fname}')
            return

        # Basic format validation: check if file starts with expected header
        try:
            with open(self.cnl_fname, 'r') as f:
                first_line = f.readline().strip()
                if not first_line.startswith('FILE_TYPE'):
                    self.log_message('WARNING: File may not be a valid Cadence Netlist (missing FILE_TYPE header)')
        except IOError as e:
            messagebox.showerror("Error", f"Cannot read file:\n{str(e)}")
            self.log_message(f'ERROR: Cannot read file: {str(e)}')
            return

        self.update_and_save_config()

        try:
            self.log_message('=' * 60)
            self.log_message(f'Starting format at {datetime.datetime.now().strftime("%H:%M:%S")}')
            self.log_message(f'Input file: {self.cnl_fname}')

            # Parse Netlist
            self.log_message('Parsing Netlist file...')
            n = AllegroNetList(self.cnl_fname)

            # Generate report
            self.log_message('Generating formatted report...')
            s = n.all_data2string()

            # Write output
            fname = self.output_fname
            self.write2newfile(fname, s)

            work_dir = Path.cwd()
            output_path = work_dir / fname

            self.log_message(f'SUCCESS: Report written to: {output_path}')
            self.log_message(f'Completed at {datetime.datetime.now().strftime("%H:%M:%S")}')
            self.log_message('=' * 60)

        except (IOError, OSError) as e:
            error_msg = f'ERROR: File I/O error: {str(e)}'
            self.log_message(error_msg)
            self.log_message('=' * 60)
            messagebox.showerror("File Error", f"Failed to read or write file:\n\n{str(e)}")
        except ValueError as e:
            error_msg = f'ERROR: Invalid file format or data: {str(e)}'
            self.log_message(error_msg)
            self.log_message('=' * 60)
            messagebox.showerror("Format Error", f"File format is invalid:\n\n{str(e)}")
        except Exception as e:
            # Catch unexpected errors but log them differently
            error_msg = f'ERROR: Unexpected error during formatting: {str(e)}'
            self.log_message(error_msg)
            self.log_message('=' * 60)
            messagebox.showerror("Unexpected Error", f"An unexpected error occurred:\n\n{str(e)}\n\nPlease report this issue.")

    def select_netlist(self) -> None:
        """GUI to select Netlist"""
        fname = askopenfilename(filetypes=(("Cadence Netlist", "pstxnet.dat"),
                                           ("All files", "*.*")))
        if fname != '':
            self.cnl_fname = fname
            self.update_self2gui()
            self.log_message(f'Selected input file: {fname}')

    def save_and_exit(self) -> None:
        """save configuration data and exit"""
        self.update_and_save_config()
        self.quit()

    def log_message(self, message: str) -> None:
        """Add message to log text widget"""
        self.log_text.config(state=NORMAL)
        self.log_text.insert(END, message + '\n')
        self.log_text.see(END)  # Auto-scroll to bottom
        self.log_text.config(state=DISABLED)
        self.update_idletasks()  # Update GUI immediately

    def clear_log(self) -> None:
        """Clear the log text widget"""
        self.log_text.config(state=NORMAL)
        self.log_text.delete(1.0, END)
        self.log_text.config(state=DISABLED)
        self.log_message('Log cleared.')

    def _open_with_system_app(self, path: str | Path) -> None:
        """Open a file or directory with the system's default application.

        Args:
            path: Path to file or directory to open

        Raises:
            OSError: If opening fails (command not found, permission denied, etc.)
        """
        try:
            path_str = str(path)
            match sys.platform:
                case 'win32':
                    import os
                    os.startfile(path_str)
                case 'darwin':  # macOS
                    ret = subprocess.call(['open', path_str])
                    if ret != 0:
                        raise OSError(f'open command failed with return code {ret}')
                case _:  # linux and other Unix-like systems
                    ret = subprocess.call(['xdg-open', path_str])
                    if ret != 0:
                        raise OSError(f'xdg-open command failed with return code {ret}')
        except OSError as e:
            # Handle case where command doesn't exist
            raise OSError(f'Failed to open with system application: {e}')

    def open_output_file(self) -> None:
        """Open the output report file"""
        output_path = Path.cwd() / self.output_fname

        if not output_path.exists():
            messagebox.showwarning("File Not Found",
                                 f"Output file does not exist yet:\n{output_path}\n\nPlease format the Netlist first.")
            self.log_message(f'Cannot open output file - file does not exist: {output_path}')
            return

        try:
            self._open_with_system_app(output_path)
            self.log_message(f'Opened output file: {output_path}')
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open file:\n{e}")
            self.log_message(f'ERROR: Failed to open output file: {e}')

    def open_output_dir(self) -> None:
        """Open the output directory in file manager"""
        work_dir = Path.cwd()

        try:
            self._open_with_system_app(work_dir)
            self.log_message(f'Opened output directory: {work_dir}')
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open directory:\n{e}")
            self.log_message(f'ERROR: Failed to open directory: {e}')

    def write2newfile(self, fname: str | Path, s: str) -> None:
        """Write data to file with two-phase commit to prevent data loss.

        Uses atomic write pattern:
        1. Write to temporary file
        2. If successful, rename old file (if exists)
        3. Rename temp file to target name
        4. If anything fails, restore old file

        Args:
            fname: Target filename
            s: Data to write
        """
        file_path = Path(fname)
        temp_path = file_path.with_suffix(file_path.suffix + '.tmp')
        old_path: Optional[Path] = None

        try:
            # Phase 1: Write to temporary file
            self.write2file(temp_path, s)

            # Phase 2: Rename old file if it exists
            if file_path.exists():
                for i in range(1, 100):
                    backup_path = Path(f'{fname},{i:02d}')
                    if not backup_path.exists():
                        file_path.rename(backup_path)
                        old_path = backup_path
                        self.log_message(f'Renamed old file to: {backup_path}')
                        break
                else:
                    # Reached max backups, cleanup temp and raise error
                    temp_path.unlink()
                    raise IOError('Too many backup files (99+). Please clean up old backups.')

            # Phase 3: Rename temp file to target name
            temp_path.rename(file_path)

        except (IOError, OSError) as e:
            # Rollback: Try to restore old file if we renamed it
            if old_path and old_path.exists() and not file_path.exists():
                try:
                    old_path.rename(file_path)
                    self.log_message(f'ERROR: Write failed, restored original file: {e}')
                except (IOError, OSError):
                    self.log_message(f'CRITICAL: Write failed AND could not restore original file: {e}')
            else:
                self.log_message(f'ERROR: Write operation failed: {e}')

            # Clean up temp file if it exists
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except (IOError, OSError):
                    pass

            raise  # Re-raise the exception for caller to handle

    def write2file(self, fname: str | Path, s: str) -> None:
        """write data to file"""
        with open(fname, 'w') as f:
            f.write(s)


if __name__ == '__main__':
    CadenceNetListFormat().mainloop()
