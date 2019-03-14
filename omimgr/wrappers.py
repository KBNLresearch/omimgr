#! /usr/bin/env python3
"""wrapper functions for readom and ddrescue"""

import logging
import time
import subprocess as sub


def readom(args):
    """readom wapper function"""

    errorFlag = False

    try:
        p = sub.Popen(args, stdout=sub.PIPE, stderr=sub.PIPE,
                      shell=False, bufsize=1, universal_newlines=True)

        # Processing of output adapted from DDRescue-GUI by Hamish McIntyre-Bhatty:
        # https://git.launchpad.net/ddrescue-gui/tree/DDRescue_GUI.py

        line = ""
        char = " "

        # Give readom plenty of time to start.
        time.sleep(2)

        # Grab information from readom. (After readom exits, attempt to keep reading chars until
        # the last attempt gave an empty string)
        while p.poll() is None or char != "":
            char = p.stderr.read(1)
            line += char

            # If this is the end of the line, process it, and send the results to the logger
            if char == "\n":
                tidy_line = line.replace("\n", "").replace("\r", "").replace("\x1b[A", "")

                if tidy_line != "":
                    # Scan output for any error references
                    if "error" in tidy_line.lower():
                        errorFlag = True
                    try:
                        logging.info(tidy_line)
                    except:
                        raise
                        # Handle unexpected errors.
                        logging.warning("Error parsing readom output!")

                #Reset line.
                line = ""

        # Parse any remaining lines afterwards.
        if line != "":
            tidy_line = line.replace("\n", "").replace("\r", "").replace("\x1b[A", "")
            logging.info(tidy_line)

        p.wait()
        exitStatus = p.returncode

    except Exception:
        raise
        # I don't even want to to start thinking how one might end up here ...
        exitStatus = -99

    # Logging
    cmdName = args[0]
    cmdLine = ' '.join(args)
    logging.info('Command: ' + cmdLine)

    if exitStatus == 0:
        logging.info(cmdName + ' status: ' + str(exitStatus))
        logging.info(cmdName + ' errorFlag: ' + str(errorFlag))
    else:
        logging.error(cmdName + ' status: ' + str(exitStatus))
        logging.info(cmdName + ' errorFlag: ' + str(errorFlag))

    return cmdLine, exitStatus, errorFlag


def ddrescue(args):
    """ddrescue wapper function"""

    errorFlag = False

    try:
        p = sub.Popen(args, stdout=sub.PIPE, stderr=sub.PIPE,
                      shell=False, bufsize=1, universal_newlines=True)

        # Processing of output adapted from DDRescue-GUI by Hamish McIntyre-Bhatty:
        # https://git.launchpad.net/ddrescue-gui/tree/DDRescue_GUI.py

        line = ""
        char = " "

        # Give ddrescue plenty of time to start.
        time.sleep(2)

        # Grab information from ddrescue. (After ddrescue exits, attempt to keep reading chars until
        # the last attempt gave an empty string)
        while p.poll() is None or char != "":
            char = p.stdout.read(1)
            line += char

            # If this is the end of the line, process it, and send the results to the logger
            if char == "\n":
                tidy_line = line.replace("\n", "").replace("\r", "").replace("\x1b[A", "")

                if tidy_line != "":
                    try:
                        logging.info(tidy_line)
                    except:
                        raise
                        # Handle unexpected errors. Can happen once in normal operation on
                        # ddrescue v1.22+
                        logging.warning("Error parsing ddrescue output!")

                #Reset line.
                line = ""

        # Parse any remaining lines afterwards.
        if line != "":
            tidy_line = line.replace("\n", "").replace("\r", "").replace("\x1b[A", "")
            logging.info(tidy_line)

        p.wait()
        exitStatus = p.returncode

    except Exception:
        raise
        # I don't even want to to start thinking how one might end up here ...
        exitStatus = -99

    # Logging
    cmdName = args[0]
    cmdLine = ' '.join(args)
    logging.info('Command: ' + cmdLine)

    if exitStatus == 0:
        logging.info(cmdName + ' status: ' + str(exitStatus))
        logging.info(cmdName + ' errorFlag: ' + str(errorFlag))
    else:
        logging.error(cmdName + ' status: ' + str(exitStatus))
        logging.info(cmdName + ' errorFlag: ' + str(errorFlag))

    return cmdLine, exitStatus, errorFlag


def umount(args):
    """umount wapper function"""
    try:
        p = sub.Popen(args, stdout=sub.PIPE, stderr=sub.PIPE, shell=False)
        output, errors = p.communicate()

        # Decode output to UTF8
        outputAsString = output.decode('utf-8')
        errorsAsString = errors.decode('utf-8')

        exitStatus = p.returncode

    except Exception:
        # I don't even want to to start thinking how one might end up here ...
        exitStatus = -99
        outputAsString = ""
        errorsAsString = ""

    # Logging
    cmdName = args[0]
    cmdLine = ' '.join(args)
    logging.info('Command: ' + cmdLine)

    # Umount returns exit status 1 if device not mounted. This is no reason
    # for any concern, so don't report this as an error in the log.
    logging.info(cmdName + ' status: ' + str(exitStatus))
    logging.info(cmdName + ' stdout:\n' + outputAsString)
    logging.info(cmdName + ' stderr:\n' + errorsAsString)

    return cmdLine, exitStatus

def generic(args):
    """generic wapper function for tools that don't require any special text processing"""
    try:
        p = sub.Popen(args, stdout=sub.PIPE, stderr=sub.PIPE, shell=False)
        output, errors = p.communicate()

        # Decode output to UTF8
        outputAsString = output.decode('utf-8')
        errorsAsString = errors.decode('utf-8')

        exitStatus = p.returncode

    except Exception:
        # I don't even want to to start thinking how one might end up here ...
        exitStatus = -99
        outputAsString = ""
        errorsAsString = ""

    # Logging
    cmdName = args[0]
    cmdLine = ' '.join(args)
    logging.info('Command: ' + cmdLine)

    if exitStatus == 0:
        logging.info(cmdName + ' status: ' + str(exitStatus))
        logging.info(cmdName + ' stdout:\n' + outputAsString)
        logging.info(cmdName + ' stderr:\n' + errorsAsString)
    else:
        logging.error(cmdName + ' status: ' + str(exitStatus))
        logging.error(cmdName + ' stdout:\n' + outputAsString)
        logging.error(cmdName + ' stderr:\n' + errorsAsString)

    return cmdLine, exitStatus