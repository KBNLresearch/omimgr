# omimgr

**Omimgr** provides a simple GUI-based workflow for making ISO images from optical media (CD-ROMs and DVDs). It wraps around the *readom* (part of [*Cdrkit*](https://en.wikipedia.org/wiki/Cdrkit)) and [*ddrescue*](https://linux.die.net/man/1/ddrescue) tools. After the imaging is done it also generates a checksum file with SHA-512 hashes of the extracted files. 


## System requirements

*Omimgr* is currently only available for Linux. So far it has been tested with Ubuntu 18.04 LTS (Bionic) and Linux Mint 18.3, which is based on Ubuntu 16.04 (Xenial). In addition it has the following dependencies:

- **Python 3.2 or more recent** (Python 2.x is not supported)

- **Tkinter**. If *tkinter* is not installed already, you need to use the OS's package manager to install (there is no PyInstaller package for *tkinter*). If you're using *apt* this should work:

        sudo apt-get install python3-tk

- **readom**, which is part of the *wodim* package. Use the following command to install it:

        sudo apt install wodim

- **ddrescue**, which can be installed using:

        sudo apt install gddrescue

## Installation

### Global install

For a global (all-users) installation run the following command:

    sudo pip3 install omimgr

Then run:

    sudo omimgr-config

If all goes well this should result in the following output:

    INFO: writing configuration file /etc/omimgr/omimgr.json
    INFO: creating desktop file /usr/share/applications/omimgr.desktop
    INFO: omimgr configuration completed successfully!

### User install

Use the following command for a single-user installation:

    pip3 install --user omimgr

Then run:

    ~/.local/bin/omimgr-config

Result:

    INFO: writing configuration file /home/johan/.config/omimgr/omimgr.json
    INFO: creating desktop file /home/johan/.local/share/applications/omimgr.desktop
    INFO: omimgr configuration completed successfully!

*Omimgr* is now ready to roll!

## Basic operation

You can start *omimgr* from the OS's main menu (in Ubuntu 18.04 the *omimgr* item is located under *System Tools*). Depending on your distro, you might get an "Untrusted application launcher" warning the first time you activate the shortcut. You can get rid of this by clicking on "Mark as Trusted". On startup the main *omimgr* window appears:

![](./img/omimgr-1.png)

Use the *Select Output Directory* button to navigate to an (empty) directory where the output files are to be stored. The interface allows you to specify the following options:

|Option|Description|
|:-|:-|
|**Optical Device**|The optical devices that is used (default: `/dev/nst0`).|
|**Read command**|The command that is used to read the disc (default: `readom`).|
|**Prefix**|Output prefix (default: `disc`).|
|**Extension**|Output file extension (default: `iso`).|
|**Retries**|Maximum number of retries (default: `4`).|
|**Direct disc mode**|Check this option to read a disc in direct disc mode (setting only has effect with *ddrescue*) (disabled by default).|
|**Identifier**|Unique identifier. You can either enter an existing identifier yourself, or press the *UUID* button to generate a [Universally unique identifier](https://en.wikipedia.org/wiki/Universally_unique_identifier).|
|**Description**|A text string that describes the tape (e.g. the title that is written on its inlay card).|
|**Notes**|Any additional info or notes you want to record with the disc.|

Press the *Start* button to start imaging a disc. You can monitor the progress of the extraction procedure in the progress window:

![](./img/omimgr-2.png)

Note that the screen output is also written to a log file in the output directory. A prompt appears when the imaging is finished:

![](./img/omimgr-success.png)

If the extraction finished without any errors, the output directory now contains the following files:

![](./img/omimgr-files.png)

Here, **file000001.dd** through **file000003.dd** are the extracted files; **checksums.sha512** contains the SHA512 checksums of the extracted files, **metadata.json** contains some basic metadata and **omimgr.log** is the log file.

If *readom*'s attempt to read the disc resulted in any errors, *omimgr* prompts the user to try again with *ddrescue*:

![](./img/errors-readom.png)

After clicking *Yes*, *omimgr* will delete the disc image that was created by *readom*, and then start *ddrescue*. If *ddrescue* also exits with any errors, it is possible to do one or more addition rounds with *ddrescue*:

![](./img/error-ddrescue.png)

After clicking *Yes*, you can activate *Direct Disc* mode, or select another optical drive. Press the *Start* button again to start reading the disc. Importantly, *omimgr* does not delete the existing disc image in this case, but it will update it with any additional data that can be rescued from the disc.

## Metadata file

The file *metadata.json* contains metadata in JSON format. Below is an example:

    {
        "acquisitionEnd": "2019-01-21T13:26:38.813304+01:00",
        "acquisitionStart": "2019-01-21T13:25:53.570770+01:00",
        "checksumType": "SHA-512",
        "checksums": {
            "file000001.dd": "e58279519cd394870f7d39fe59d722bf85c64fb95a9b4c8a893fde0a606f5e270529d17d0598d9e703f9b259a2355c91aaa3721249a64982e580f2f18e6e52f5",
            "file000002.dd": "19f200700afeab90d45d3beec0cdaf5290ca517574b9049feee80d1257c5d11677d9ecd101c31e30b02d58b4d84c8cac0ea7326d10342d1d7ea4ce40dde663ca",
            "file000003.dd": "9f4f5ea7cc3639c07ca88b4dcda9b976d2802d229a26415d960962d4fdc2d920ea1ce554343dfc5f22c3c616cad3977e24ddf33c86417dc0112a8560e2f1e75f"
        },
        "description": "Test tape October 25 2018",
        "extension": "dd",
        "files": "",
        "fillBlocks": false,
        "identifier": "2d257dec-1d77-11e9-9594-2c4138b5272c",
        "initBlockSize": 512,
        "notes": "This tape only contains some old rubbish. Created specifically for testing omimgr.",
        "prefix": "file",
        "successFlag": true,
        "tapeDevice": "/dev/nst0",
        "tapeimagrVersion": "0.4.0b1"
    }

## Configuration file

*Omimgr*'s internal settings (default values for output file names, tape device, etc.) are defined in a configuration file in Json format. For a global installation it is located at */etc/omimgr/omimgr.json*; for a user install it can be found at *~/.config/omimgr/omimgr.json*. The default configuration is show below:

    {
        "checksumFileName": "checksums.sha512",
        "defaultDir": "",
        "extension": "dd",
        "files": "",
        "fillBlocks": "False",
        "initBlockSize": "512",
        "logFileName": "omimgr.log",
        "metadataFileName": "metadata.json",
        "prefix": "file",
        "tapeDevice": "/dev/nst0",
        "timeZone": "Europe/Amsterdam"
    }

You can change *omimgr*'s default settings by editing this file. Most of the above settings are self-explanatory, with the exception of the following:

- **defaultDir**: this allows you to change the default file path that is opened after pressing *Select Output Directory*. By default *omimgr* uses the current user's home directory. However, if *defaultDir* points to a valid directory path, that directory is used instead.

- **timeZone**: time zone string that is used to correctly format the *acquisitionStart* and *acquisitionEnd* date/time strings. You can adapt it to your own location by using the *TZ database name* from [this list of tz database time zones](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones).

Note that it is *not* recommended to change the value of *initBlockSize*, as it may result in unexpected behaviour. If you accidentally messed up the configuration file, you can always restore the original one by running the *omimgr-config* tool again.

## Uninstalling omimgr

To remove *omimgr*, first run the *omimgr-config* with the `--remove` flag to remove the configuration file and the start menu and desktop files. For a global install, run:

    sudo omimgr-config --remove

For a user install, run:

    ~/.local/bin/omimgr-config --remove

The resulting output (shown below for a user install):

    INFO: removing configuration file /home/johan/.config/omimgr/omimgr.json
    INFO: removing configuration directory /home/johan/.config/omimgr
    INFO: removing desktop file /home/johan/.local/share/applications/omimgr.desktop
    INFO: omimgr configuration completed successfully!

Then remove the Python package with following command (global install):

    sudo pip3 uninstall omimgr

For a user install use this:

    pip3 uninstall omimgr

## Contributors

Written by Johan van der Knijff. Some parts of the code that processes ddrescue's and readom's terminal output were adapted from [DDRescue-GUI](https://launchpad.net/ddrescue-gui) by Hamish McIntyre-Bhatty.

## License

*Omimgr* is released under the  Apache License 2.0.
