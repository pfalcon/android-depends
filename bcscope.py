#!/usr/bin/env python
# -*- coding: utf-8 -*-

__VERSION__ = '1.0.1'
__author__ = 'rx.wen218@gmail.com'

import subprocess
import sys
import shutil
import os
from optparse import OptionParser

SUCCESS = 0
file_list_name = "cscope.files"
default_database_name = "cscope.out"
default_cfg_name = ".bcscope.cfg"

# parse command line options
opt_parser = OptionParser(version = "%prog " + __VERSION__, 
            description = "command line tool for generating cscope database",
            usage = "%prog [-o file] [file type: c++(default)/python/java]")
opt_parser.add_option("-o", "--output", dest="output_file", default=default_database_name, help="cscope database file")
opt_parser.add_option("-i", "--input", dest="input_file", default=default_cfg_name, help="cfg file lists all directories to be searched")
opt_parser.add_option("-r", "--recursive", action="store_true", default=False, help="recursivly include input_file contained in all directories [default: %default]")
opt_parser.add_option("-v", "--verbose", action="store_true", default=False, help="verbose output [default: %default]")
opt_parser.add_option("-a", "--absolute", action="store_true", default=False, help="generate cscope database with absolute path [default: %default]")
opt_parser.add_option("-c", "--confirm", action="store_true", default=False, help="confirm overwrite existing cscope database without interaction [default: %default]")
(cmdline_options, args) = opt_parser.parse_args()

# config application behavior
valid_lan_types = {"c++": ".+\.\(cpp\|c\|cxx\|cc\|h\|hpp\|hxx\)$",
    "java": ".+\.java$",
    "python": ".+\.py$"}
lan_type = "c++"
if len(args) > 0:
    lan_type = args[0]
if valid_lan_types.has_key(lan_type):
    lan_pattern = valid_lan_types[lan_type]
else:
    print "invalid language type: " + lan_type
    print "must be one of:"
    for (k, v) in valid_lan_types.items():
        print "\t" + k
    sys.exit(-1)

# take care of accidently overwrite existing database file
if not cmdline_options.confirm:
    confirm = 'n'
    if default_database_name != cmdline_options.output_file and os.path.isfile(default_database_name):
       confirm = raw_input(default_database_name + " already exists, overwrite it? (y/n)")
       if confirm != "y":
           sys.exit(0)
    if os.path.isfile(cmdline_options.output_file):
       confirm = raw_input(cmdline_options.output_file + " already exists, overwrite it? (y/n)")
       if confirm != "y":
           sys.exit(0)

file_list = open(file_list_name, "w")
# should we check more directories?
dirs = []
def include_dirs_from_cfg(cfg_file, search_dirs):
    if os.path.isfile(cfg_file):
        if cmdline_options.verbose:
            print "read configuration file from " + cfg_file
        f = open(cfg_file)
        for line in f:
            line = line.strip() # remove possible \n char
            if len(line) > 0 and not line.startswith("#"):
                line = os.path.expanduser(line)
                if os.path.isdir(line):
                    if search_dirs.count(line) == 0:
                        search_dirs.append(line)
                elif cmdline_options.verbose:
                    print line + " is not a directory, omit it"
        f.close()

include_dirs_from_cfg(cmdline_options.input_file, dirs)

# find source files in all directories
def naive_find_for_win(d, pattern, file_list):
    """
    a naive implementation of find for windows
    we do this for two reasons:
    1. unix find isn't widely available on windows
    2. even if we manually install unix find, the windows's own find take precedence over it.
        because the CreateProcess api called by Popen will search system directory
        first, then PATH environment variable. So, windows's own find will be executed
    """
    import re
    def func(arg, dirname, fnames):
        arg = arg + dirname + os.sep
        for f in fnames:
            fpath = arg+f
            if os.path.isfile(fpath):
                if re.match(pattern, fpath):
                    source_files.append(fpath + "\n")
            #    fnames.remove(f)
    source_files = []
    os.path.walk(d, func, "")
    file_list.writelines(source_files)

if cmdline_options.recursive:
# include cfg files in other directories
    for d in dirs:
        include_dirs_from_cfg(d+os.path.sep+cmdline_options.input_file, dirs)

# make sure current directory is included
if dirs.count(".") + dirs.count("./") < 1:
    dirs.insert(0, ".")

for d in dirs:
    if cmdline_options.absolute:
        d = os.path.abspath(d) + os.path.sep
    print "find " + lan_type + " source files in " + d
    if sys.platform != "win32":
        subprocess.Popen(["find", d, "-iregex", lan_pattern], stdout=file_list).wait()
    else:
        # change lan_pattern so that it works on python
        lan_pattern = lan_pattern.replace("\(", "(").replace("\)", ")").replace("\|", "|")
        naive_find_for_win(d, lan_pattern, file_list)
file_list.close()

# actually generate database
print "build cscope database"
subprocess.Popen(["cscope", "-b"]).wait()
if cmdline_options.output_file != default_database_name:
    shutil.move(default_database_name, cmdline_options.output_file)
os.remove(file_list_name)
print "done, cscope database saved in " + cmdline_options.output_file

