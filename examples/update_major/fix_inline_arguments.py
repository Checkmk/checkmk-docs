#!/usr/bin/env python3

# Copyright (C) 2023 Checkmk GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.

# Modify inline argument case insensitive from the syntax allowed in Python 3.10 to the
# stricter syntax of Python 3.11. Call with the file to modify as argument.
# Use on your own risk.

# Probably only needed for updating from Checkmk 2.1.0 to 2.2.0.

import re
import shutil
import sys

def create_backup(fpath):
    bpath = fpath + ".bak"
    shutil.copyfile(fpath, bpath)

def modify_lines(fpath):
    bpath = fpath + ".bak"
    o = open(fpath, "w")
    with open(bpath) as f:
        for line in f:
            if re.search(r'\(\?i\)', line):
                print("OLD> " + line)
                line = re.sub(r'\(\?i\)(.*?)\'', r"(?i:\1)'", line)
                print("NEW> " + line)
            o.write(line)
    o.close

create_backup(sys.argv[1])
modify_lines(sys.argv[1]) 