#! /usr/bin/env python3
"""This module contains the Disc class with functions that
do the actual imaging.
"""

import os
import io
import json
import time
import logging
import glob
import pathlib
from shutil import which
from . import config
from . import shared

class Disc:
    """Disc class"""
    def __init__(self):
        """initialise Disc class instance"""

        # Input collected by GUI / CLI
        self.dirOut = ''
        self.omDevice = ''
        self.readCommand = ''
        self.retries = ''
        self.prefix = ''
        self.extension = ''
        self.rescueDirectDiscMode = ''
        self.retriesDefault = ''
        self.identifier = ''
        self.description = ''
        self.notes = ''
        # Input validation flags
        self.dirOutIsDirectory = False
        self.outputExistsFlag = False
        self.deviceExistsFlag = False
        self.dirOutIsWritable = False
        # Flags that define if dependencies are installed
        self.ddrescueInstalled = False
        self.readomInstalled = False
        # Config file location, depends on package directory
        packageDir = os.path.dirname(os.path.abspath(__file__))
        homeDir = os.path.normpath(os.path.expanduser("~"))
        if packageDir.startswith(homeDir):
            self.configFile = os.path.join(homeDir, '.config/omimgr/omimgr.json')
        else:
            self.configFile = os.path.normpath('/etc/omimgr/omimgr.json')

        # Miscellaneous attributes
        self.logFile = ''
        self.imageFile = ''
        self.logFileName = ''
        self.checksumFileName = ''
        self.metadataFileName = ''
        self.finishedFlag = False
        self.omDeviceIOError = False
        self.successFlag = True
        self.configSuccess = True
        self.timeZone = ''
        self.defaultDir = ''

    def getConfiguration(self):
        """read configuration file and set variables accordingly"""
        if not os.path.isfile(self.configFile):
            self.configSuccess = False

        # Read config file to dictionary
        try:
            with io.open(self.configFile, 'r', encoding='utf-8') as f:
                configDict = json.load(f)
        except:
            self.configSuccess = False

        if self.configSuccess:
            # Update class variables
            try:
                self.logFileName = configDict['logFileName']
                self.checksumFileName = configDict['checksumFileName']
                self.metadataFileName = configDict['metadataFileName']
                self.omDevice = configDict['omDevice']
                self.prefix = configDict['prefix']
                self.extension = configDict['extension']
                self.rescueDirectDiscMode = configDict['rescueDirectDiscMode']
                self.retriesDefault = configDict['retries']
                self.timeZone = configDict['timeZone']
                self.defaultDir = configDict['defaultDir']
            except KeyError:
                self.configSuccess = False


    def validateInput(self):
        """Validate and pre-process input"""

        # Check if dirOut is a directory
        self.dirOutIsDirectory = os.path.isdir(self.dirOut)

        # Check if glob pattern for dirOut, prefix and extension matches existing files
        if glob.glob(self.dirOut + '/' + self.prefix + '*.' + self.extension):
            self.outputExistsFlag = True

        # Check if dirOut is writable
        self.dirOutIsWritable = os.access(self.dirOut, os.W_OK | os.X_OK)

        # Check if readom and ddrescue are installed

        if which("readom") is not None:
            self.readomInstalled = True
        if which("ddrescue") is not None:
            self.ddrescueInstalled = True

        # Check if selected block device exists
        p = pathlib.Path(self.omDevice)
        self.deviceExistsFlag = p.is_block_device()

        # Convert rescueDirectDiscMode to Boolean
        self.rescueDirectDiscMode = bool(self.rescueDirectDiscMode)

        # Image file
        self.imageFile = os.path.join(self.dirOut, self.prefix + '.' + self.extension)

        # Log file
        self.logFile = os.path.join(self.dirOut, self.logFileName)

    def processDisc(self):
        """Process a disc"""

        # Create dictionary for storing metadata (which are later written to file)
        metadata = {}

        # Write some general info to log file
        logging.info('***************************')
        logging.info('*** OMIMGR EXTRACTION LOG ***')
        logging.info('***************************\n')
        logging.info('*** USER INPUT ***')
        logging.info('omimgrVersion: ' + config.version)
        logging.info('dirOut: ' + self.dirOut)
        logging.info('omDevice: ' + self.omDevice)
        logging.info('readCommand: ' + self.readCommand)
        logging.info('maxRetries: ' + str(self.retries))
        logging.info('prefix: ' + self.prefix)
        logging.info('extension: ' + self.extension)
        logging.info('direct disc mode (ddrescue only): ' + str(self.rescueDirectDiscMode))
    
        ## Acquisition start date/time
        acquisitionStart = shared.generateDateTime(self.timeZone)

        # Unmount disc
        args = ['umount', self.omDevice]
        umountStatus, umountOut, umountErr = shared.launchSubProcess(args)

        if self.readCommand == "readom":
            args = ['readom']
            args.append('retries=' + str(self.retries))
            args.append('dev=' + self.omDevice)
            args.append('f=' + self.imageFile)

        readStatus, readOut, readErr = shared.launchSubProcess(args)

        # Create checksum file
        logging.info('*** Creating checksum file ***')
        checksumFile = os.path.join(self.dirOut, self.checksumFileName)
        writeFlag, checksums = shared.checksumDirectory(self.dirOut, self.extension, checksumFile)

        # Acquisition end date/time
        acquisitionEnd = shared.generateDateTime(self.timeZone)

        # Fill metadata dictionary
        metadata['identifier'] = self.identifier
        metadata['description'] = self.description
        metadata['notes'] = self.notes
        metadata['omimgrVersion'] = config.version
        metadata['omDevice'] = self.omDevice
        metadata['readCommand'] = self.readCommand
        metadata['maxRetries'] = self.retries
        metadata['rescueDirectDiscMode'] = str(self.rescueDirectDiscMode)
        metadata['prefix'] = self.prefix
        metadata['extension'] = self.extension
        metadata['acquisitionStart'] = acquisitionStart
        metadata['acquisitionEnd'] = acquisitionEnd
        metadata['successFlag'] = self.successFlag
        metadata['checksums'] = checksums
        metadata['checksumType'] = 'SHA-512'

        # Write metadata to file in json format
        logging.info('*** Writing metadata file ***')
        metadataFile = os.path.join(self.dirOut, self.metadataFileName)
        try:
            with io.open(metadataFile, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=4, sort_keys=True)
        except IOError:
            self.successFlag = False
            logging.error('error while writing metadata file')

        logging.info('Success: ' + str(self.successFlag))

        if self.successFlag:
            logging.info('Disc processed successfully without errors')
        else:
            logging.error('One or more errors occurred while processing disc, \
            check log file for details')

        # Set finishedFlag
        self.finishedFlag = True

        # Wait 2 seconds to avoid race condition
        time.sleep(2)
