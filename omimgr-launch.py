#! /usr/bin/env python

"""Wrapper script, ensures that relative imports work correctly in a PyInstaller build"""

from omimgr.omimgr import main

if __name__ == '__main__':
    main()
