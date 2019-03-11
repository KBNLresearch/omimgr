#! /usr/bin/env python3
"""
ommgr, automated reading of optical media
Graphical user interface

Author: Johan van der Knijff
Research department,  KB / National Library of the Netherlands
"""

import sys
import os
import time
import threading
import logging
import queue
import uuid
import tkinter as tk
from tkinter import filedialog as tkFileDialog
from tkinter import scrolledtext as ScrolledText
from tkinter import messagebox as tkMessageBox
from tkinter import ttk
from .om import Disc
from . import config


class omimgrGUI(tk.Frame):

    """This class defines the graphical user interface + associated functions
    for associated actions
    """

    def __init__(self, parent, *args, **kwargs):
        """Initiate class"""
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.root = parent
        # Logging stuff
        self.logger = logging.getLogger()
        # Create a logging handler using a queue
        self.log_queue = queue.Queue(-1)
        self.queue_handler = QueueHandler(self.log_queue)
        # Create disc instance
        self.disc = Disc()
        self.t1 = None
        # Read configuration file
        self.disc.getConfiguration()
        # Set dirOut, depending on whether value from config is a directory
        if os.path.isdir(self.disc.defaultDir):
            self.disc.dirOut = self.disc.defaultDir
        else:
            self.disc.dirOut = os.path.expanduser("~")
        # Build the GUI
        self.build_gui()

    def on_quit(self):
        """Quit omimgr"""
        os._exit(0)

    def on_submit(self):
        """fetch and validate entered input, and start processing"""

        # This flag is true if all input validates
        inputValidateFlag = True

        # Fetch entered values (strip any leading / trailing whitespace characters)
        self.disc.omDevice = self.omDevice_entry.get().strip()
        rcItems = self.readCommand_entry.get(0, tk.END) # Tuple of all selection items
        rcSel = self.readCommand_entry.curselection() # Tuple with index of selected item
        self.disc.readCommand = rcItems[rcSel[0]]
        self.disc.retries = self.retries_entry.get().strip()
        self.disc.prefix = self.prefix_entry.get().strip()
        self.disc.extension = self.extension_entry.get().strip()
        self.disc.identifier = self.identifier_entry.get().strip()
        self.disc.description = self.description_entry.get(1.0, tk.END).strip()
        self.disc.notes = self.notes_entry.get(1.0, tk.END).strip()
        #self.disc.rescueDirectDiscMode = self.rescueDirectDiscMode.get()
        self.disc.rescueDirectDiscMode = self.rescueDirectDiscMode.get()
        ## TEST
        uInput = [self.disc.omDevice, self.disc.readCommand, self.disc.prefix,
                  self.disc.extension, self.disc.retries, self.disc.rescueDirectDiscMode,
                  self.disc.identifier, self.disc.description, self.disc.notes]
        for item in uInput:
            print(item)
        ## TEST

        # Validate input
        self.disc.validateInput()

        # Show error message for any parameters that didn't pass validation
        if not self.disc.dirOutIsDirectory:
            inputValidateFlag = False
            msg = ("Output directory doesn't exist:\n" + self.disc.dirOut)
            tkMessageBox.showerror("ERROR", msg)

        if not self.disc.dirOutIsWritable:
            inputValidateFlag = False
            msg = ('Cannot write to directory ' + self.disc.dirOut)
            tkMessageBox.showerror("ERROR", msg)

        if not self.disc.deviceExistsFlag:
            inputValidateFlag = False
            msg = ('Selected device is not accessible')
            tkMessageBox.showerror("ERROR", msg)
        
        if not self.disc.readomInstalled:
            inputValidateFlag = False
            msg = ('readom not installed')
            tkMessageBox.showerror("ERROR", msg)
    
        if not self.disc.ddrescueInstalled:
            inputValidateFlag = False
            msg = ('readom not installed')
            tkMessageBox.showerror("ERROR", msg)

        # Ask confirmation if output files exist already
        outDirConfirmFlag = True
        if self.disc.outputExistsFlag:
            msg = ('writing to ' + self.disc.dirOut + ' will overwrite existing files!\n'
                   'press OK to continue, otherwise press Cancel ')
            outDirConfirmFlag = tkMessageBox.askokcancel("Overwrite files?", msg)

        if inputValidateFlag and outDirConfirmFlag:

            # Start logger
            successLogger = True
            try:
                self.setupLogger()
                # Start polling log messages from the queue
                self.after(100, self.poll_log_queue)
            except OSError:
                # Something went wrong while trying to write to log file
                msg = ('error trying to write log file to ' + self.disc.logFile)
                tkMessageBox.showerror("ERROR", msg)
                successLogger = False

            if successLogger:
                # Disable start and exit buttons
                self.start_button.config(state='disabled')
                self.quit_button.config(state='disabled')

                # Launch disc processing function as subprocess
                self.t1 = threading.Thread(target=self.disc.processDisc)
                self.t1.start()


    def selectOutputDirectory(self, event=None):
        """Select output directory"""
        dirInit = self.disc.dirOut
        self.disc.dirOut = tkFileDialog.askdirectory(initialdir=dirInit)
        self.outDirLabel['text'] = self.disc.dirOut

    def decreaseRetries(self):
        """Decrease value of retries"""
        try:
            retriesOld = int(self.retries_entry.get().strip())
        except ValueError:
            # Reset if user manually entered something weird
            retriesOld = int(self.disc.retriesDefault)
        retriesNew = max(0, retriesOld - 1)
        self.retries_entry.delete(0, tk.END)
        self.retries_entry.insert(tk.END, str(retriesNew))

    def increaseRetries(self):
        """Increase value of retries"""
        try:
            retriesOld = int(self.retries_entry.get().strip())
        except ValueError:
            # Reset if user manually entered something weird
            retriesOld = int(self.disc.retriesDefault)
        retriesNew = retriesOld + 1
        self.retries_entry.delete(0, tk.END)
        self.retries_entry.insert(tk.END, str(retriesNew))

    def insertUUID(self):
        """Insert UUID into identifier field"""
        myID = str(uuid.uuid1())
        self.identifier_entry.delete(0, tk.END)
        self.identifier_entry.insert(tk.END, myID)

    def build_gui(self):
        """Build the GUI"""

        self.root.title('omimgr v.' + config.version)
        self.root.option_add('*tearOff', 'FALSE')
        self.grid(column=0, row=0, sticky='w')
        self.grid_columnconfigure(0, weight=0, pad=0)
        self.grid_columnconfigure(1, weight=0, pad=0)
        self.grid_columnconfigure(2, weight=0, pad=0)
        self.grid_columnconfigure(3, weight=0, pad=0)

        # Entry elements
        ttk.Separator(self, orient='horizontal').grid(column=0, row=0, columnspan=4, sticky='ew')
        # Output Directory
        self.outDirButton_entry = tk.Button(self,
                                            text='Select Output Directory',
                                            command=self.selectOutputDirectory,
                                            width=20)
        self.outDirButton_entry.grid(column=0, row=3, sticky='w')
        self.outDirLabel = tk.Label(self, text=self.disc.dirOut)
        self.outDirLabel.update()
        self.outDirLabel.grid(column=1, row=3, sticky='w')

        ttk.Separator(self, orient='horizontal').grid(column=0, row=4, columnspan=4, sticky='ew')

        # Device
        tk.Label(self, text='Optical device').grid(column=0, row=5, sticky='w')
        self.omDevice_entry = tk.Entry(self, width=20)
        self.omDevice_entry['background'] = 'white'
        self.omDevice_entry.insert(tk.END, self.disc.omDevice)
        self.omDevice_entry.grid(column=1, row=5, sticky='w')

        # Read command (readom or ddrescue)
        tk.Label(self, text='Read command').grid(column=0, row=6, sticky='w')
        self.readCommand_entry = tk.Listbox(self, selectmode=tk.SINGLE, height=2)
        self.readCommand_entry['background'] = 'white'
        for item in ["readom", "ddrescue"]:
            self.readCommand_entry.insert(tk.END, item)
        self.readCommand_entry.select_set(0)
        self.readCommand_entry.grid(column=1, row=6, sticky='w')

        # Prefix
        tk.Label(self, text='Prefix').grid(column=0, row=7, sticky='w')
        self.prefix_entry = tk.Entry(self, width=20)
        self.prefix_entry['background'] = 'white'
        self.prefix_entry.insert(tk.END, self.disc.prefix)
        self.prefix_entry.grid(column=1, row=7, sticky='w')

        # Extension
        tk.Label(self, text='Extension').grid(column=0, row=8, sticky='w')
        self.extension_entry = tk.Entry(self, width=20)
        self.extension_entry['background'] = 'white'
        self.extension_entry.insert(tk.END, self.disc.extension)
        self.extension_entry.grid(column=1, row=8, sticky='w')

        # Retries
        tk.Label(self, text='Retries').grid(column=0, row=9, sticky='w')
        self.retries_entry = tk.Entry(self, width=20)
        self.retries_entry['background'] = 'white'
        self.retries_entry.insert(tk.END, self.disc.retriesDefault)
        self.retries_entry.grid(column=1, row=9, sticky='w')
        self.decreaseRetriesButton = tk.Button(self, text='-', command=self.decreaseRetries, width=1)
        self.decreaseRetriesButton.grid(column=1, row=9, sticky='e')
        self.increaseRetriesButton = tk.Button(self, text='+', command=self.increaseRetries, width=1)
        self.increaseRetriesButton.grid(column=2, row=9, sticky='w')

        # Direct disc mode
        tk.Label(self, text='Direct disc mode (ddrescue)').grid(column=0, row=11, sticky='w')
        self.rescueDirectDiscMode = tk.BooleanVar()
        self.rescueDirectDiscMode.set(self.disc.rescueDirectDiscMode)
        self.rescueDirectDiscMode_entry = tk.Checkbutton(self, variable=self.rescueDirectDiscMode)
        self.rescueDirectDiscMode_entry.grid(column=1, row=11, sticky='w')

        ttk.Separator(self, orient='horizontal').grid(column=0, row=12, columnspan=4, sticky='ew')

        # Identifier entry field
        tk.Label(self, text='Identifier').grid(column=0, row=13, sticky='w')
        self.identifier_entry = tk.Entry(self, width=20)
        self.identifier_entry['background'] = 'white'
        self.identifier_entry.insert(tk.END, self.disc.identifier)
        self.identifier_entry.grid(column=1, row=13, sticky='w')
        self.uuidButton = tk.Button(self, text='UUID', command=self.insertUUID, width=2)
        self.uuidButton.grid(column=1, row=13, sticky='e')

        # Description entry field
        tk.Label(self, text='Description').grid(column=0, row=14, sticky='w')
        self.description_entry = tk.Text(self, height=2, width=35)
        self.description_entry['background'] = 'white'
        self.description_entry.insert(tk.END, self.disc.description)
        self.description_entry.grid(column=1, row=14, sticky='w', columnspan=1)

        # Notes entry field
        tk.Label(self, text='Notes').grid(column=0, row=15, sticky='w')
        self.notes_entry = tk.Text(self, height=6, width=35)
        self.notes_entry['background'] = 'white'
        self.notes_entry.insert(tk.END, self.disc.notes)
        self.notes_entry.grid(column=1, row=15, sticky='w', columnspan=1)

        ttk.Separator(self, orient='horizontal').grid(column=0, row=16, columnspan=4, sticky='ew')

        self.start_button = tk.Button(self,
                                      text='Start',
                                      width=10,
                                      underline=0,
                                      command=self.on_submit)
        self.start_button.grid(column=1, row=17, sticky='w')

        self.quit_button = tk.Button(self,
                                     text='Exit',
                                     width=10,
                                     underline=0,
                                     command=self.on_quit)
        self.quit_button.grid(column=1, row=17, sticky='e')

        ttk.Separator(self, orient='horizontal').grid(column=0, row=18, columnspan=4, sticky='ew')

        # Add ScrolledText widget to display logging info
        self.st = ScrolledText.ScrolledText(self, state='disabled', height=15)
        self.st.configure(font='TkFixedFont')
        self.st['background'] = 'white'
        self.st.grid(column=0, row=19, sticky='ew', columnspan=4)

        # Define bindings for keyboard shortcuts: buttons
        self.root.bind_all('<Control-Key-d>', self.selectOutputDirectory)
        self.root.bind_all('<Control-Key-s>', self.on_submit)
        self.root.bind_all('<Control-Key-e>', self.on_quit)

        for child in self.winfo_children():
            child.grid_configure(padx=5, pady=5)

        # Display message and exit if config file could not be read
        if not self.disc.configSuccess:
            msg = ("Error reading configuration file! \n" +
                   "Run '(sudo) omimgr-config' to fix this.")
            errorExit(msg)

    def reset_gui(self):
        """Reset the GUI"""
        # Create new tape instance
        self.disc = Disc()
        # Read configuration
        self.disc.getConfiguration()
        # Set dirOut, depending on whether value from config is a directory
        if os.path.isdir(self.disc.defaultDir):
            self.disc.dirOut = self.disc.defaultDir
        else:
            self.disc.dirOut = os.path.expanduser("~")
        # Logging stuff
        self.logger = logging.getLogger()
        # Create a logging handler using a queue
        self.log_queue = queue.Queue(-1)
        self.queue_handler = QueueHandler(self.log_queue)
        # Reset all entry widgets
        self.outDirLabel['text'] = self.disc.dirOut
        self.omDevice_entry.delete(0, tk.END)
        self.omDevice_entry.insert(tk.END, self.disc.omDevice)
        self.retries_entry.delete(0, tk.END)
        self.retries_entry.insert(tk.END, self.disc.retriesDefault)
        self.prefix_entry.delete(0, tk.END)
        self.prefix_entry.insert(tk.END, self.disc.prefix)
        self.extension_entry.delete(0, tk.END)
        self.extension_entry.insert(tk.END, self.disc.extension)
        self.identifier_entry.delete(0, tk.END)
        self.identifier_entry.insert(tk.END, self.disc.identifier)
        self.description_entry.delete(1.0, tk.END)
        self.description_entry.insert(tk.END, self.disc.description)
        self.notes_entry.delete(1.0, tk.END)
        self.notes_entry.insert(tk.END, self.disc.notes)
        self.rescueDirectDiscMode_entry.variable = self.disc.rescueDirectDiscMode
        self.start_button.config(state='normal')
        self.quit_button.config(state='normal')

    def setupLogger(self):
        """Set up logger configuration"""

        # Basic configuration
        logging.basicConfig(filename=self.disc.logFile,
                            level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s')

        # Add the handler to logger
        self.logger = logging.getLogger()

        # This sets the console output format (slightly different from basicConfig!)
        formatter = logging.Formatter('%(levelname)s: %(message)s')
        self.queue_handler.setFormatter(formatter)
        self.logger.addHandler(self.queue_handler)

    def display(self, record):
        """Display log record in scrolledText widget"""
        msg = self.queue_handler.format(record)
        self.st.configure(state='normal')
        self.st.insert(tk.END, msg + '\n', record.levelname)
        self.st.configure(state='disabled')
        # Autoscroll to the bottom
        self.st.yview(tk.END)

    def poll_log_queue(self):
        """Check every 100ms if there is a new message in the queue to display"""
        while True:
            try:
                record = self.log_queue.get(block=False)
            except queue.Empty:
                break
            else:
                self.display(record)
        self.after(100, self.poll_log_queue)


class QueueHandler(logging.Handler):
    """Class to send logging records to a queue

    It can be used from different threads
    The ConsoleUi class polls this queue to display records in a ScrolledText widget
    Taken from https://github.com/beenje/tkinter-logging-text-widget/blob/master/main.py
    """

    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        self.log_queue.put(record)


def checkDirExists(dirIn):
    """Check if directory exists and exit if not"""
    if not os.path.isdir(dirIn):
        msg = ('directory ' + dirIn + ' does not exist!')
        tkMessageBox.showerror("Error", msg)
        sys.exit(1)


def errorExit(error):
    """Show error message in messagebox and then exit after user presses OK"""
    tkMessageBox.showerror("Error", error)
    os._exit(1)


def main():
    """Main function"""

    packageDir = os.path.dirname(os.path.abspath(__file__))
    root = tk.Tk()
    root.iconphoto(True, tk.PhotoImage(file=os.path.join(packageDir, 'icons', 'omimgr.png')))
    myGUI = omimgrGUI(root)
    # This ensures application quits normally if user closes window
    root.protocol('WM_DELETE_WINDOW', myGUI.on_quit)

    while True:
        try:
            root.update_idletasks()
            root.update()
            time.sleep(0.1)
            if myGUI.disc.finishedFlag:
                myGUI.t1.join()
                #myGUI.logger.removeHandler(myGUI.queue_handler)
                #myGUI.queue_handler.close()
                handlers = myGUI.logger.handlers[:]
                for handler in handlers:
                    handler.close()
                    myGUI.logger.removeHandler(handler)

                if myGUI.disc.omDeviceIOError:
                    # Tape device not accessible
                    msg = ('Cannot access tape device ' + myGUI.disc.omDevice +
                           '. Check that device exits, and that tapeimgr is run as root')
                    errorExit(msg)
                elif myGUI.disc.successFlag:
                    # Tape extraction completed with no errors
                    msg = ('Tape processed successfully without errors')
                    tkMessageBox.showinfo("Success", msg)
                else:
                    # Tape extraction resulted in errors
                    msg = ('One or more errors occurred while processing tape, '
                           'check log file for details')
                    tkMessageBox.showwarning("Errors occurred", msg)

                # Reset the GUI
                myGUI.reset_gui()

        except Exception as e:
            # Unexpected error
            msg = 'An unexpected error occurred, see log file for details'
            logging.error(e, exc_info=True)
            errorExit(msg)

if __name__ == "__main__":
    main()
