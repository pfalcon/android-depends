#!/usr/bin/env python
# -*- coding: utf-8 -*-

__VERSION__ = '1.0.0'
__author__ = 'rx.wen218@gmail.com'
"""
android cross platform gdb wrapper
"""
import subprocess
import os
import sys
import re
from optparse import OptionParser

debugger_wrappers = ["none", "cgdb", "ddd"]
KEY_ANDROID_SRC_ROOT = "ANDROID_SRC_ROOT"
default_android_src_root = ""
if os.environ.has_key(KEY_ANDROID_SRC_ROOT):
    default_android_src_root = os.environ[KEY_ANDROID_SRC_ROOT]
gdb_port = "7890"

# parse command line options
opt_parser = OptionParser(version = "%prog " + __VERSION__, 
            description = "wrapper on android gdb",
            usage = "%prog [options] process_name")
opt_parser.add_option("", "--android-src-root", dest="android_src_root", default=default_android_src_root, 
        help="root of android source tree, can be set via "+KEY_ANDROID_SRC_ROOT+" environment variable")
opt_parser.add_option("-d", "--debugger-wrapper", dest="debugger_wrapper", default=debugger_wrappers[0], 
        help="wrappers on gdb, e.g., cgdb, ddd")
opt_parser.add_option("-p", "--port", dest="gdb_port", default=gdb_port, 
        help="port used for gdbserver, [default: %default]")
opt_parser.add_option("-v", "--verbose", action="store_true", default=False, help="verbose output [default: %default]")
(cmdline_options, args) = opt_parser.parse_args()
if len(args) < 1:
    print "must specify process name"
    sys.exit(-1)
process_name = args[0]

if cmdline_options.android_src_root == None or cmdline_options.android_src_root == "":
    print "android-src-root must be set"
    sys.exit(-1)

# find debugger
debugger_pattern = "arm-eabi-gdb"
debugger_path = ""
if sys.platform.startswith("linux"):
    debugger_pattern = ".+linux.+" + debugger_pattern
    p = subprocess.Popen(["find", cmdline_options.android_src_root+os.sep+"prebuilt", "-iregex", debugger_pattern], stdout=subprocess.PIPE)
    p.wait()
output = p.stdout.readlines()
if len(output) < 0:
    print DEBUGGER_NAME+" not found. Did you compile android source?"
    sys.exit(-1)
else:
    debugger_path = output[len(output)-1]

# find pid of target process
number_pattern = "([0-9]+) +"
process_pattern = "[a-zA-Z_0-9]+ +("+number_pattern+") +.+"+process_name
pid = "0"
p = subprocess.Popen(["adb", "shell", "ps"], stdout=subprocess.PIPE)
p.wait()
output = p.stdout.readlines()
for l in output:
    m = re.match(process_pattern, l)
    if m:
        pid = m.groups()[0]
if pid == "0":
    print process_name + " process not found"
    sys.exit(-1)

# start gdbserver
os.system("adb shell gdbserver :" + cmdline_options.gdb_port + " --attach " + pid + " &")

symbol_root = cmdline_options.android_src_root+"out/target/product/generic/symbols/"
process_symbol = ""
if sys.platform.startswith("linux"):
    process_symbol_pattern = ".+" + process_name 
    p = subprocess.Popen(["find", symbol_root, "-iregex", process_symbol_pattern], stdout=subprocess.PIPE)
    p.wait()
output = p.stdout.readlines()
# start gdb client
cmd = [debugger_path.rstrip(), output[0].rstrip(), "-ex", '"set solib-search-path ' + symbol_root 
        + 'system/lib" -ex "target remote :'+cmdline_options.gdb_port+'"']
cmdl = ""
for c in cmd:        
    cmdl += " " + c

# run gdb under cgdb 
if cmdline_options.debugger_wrapper == "cgdb":
    cmdl = "cgdb -d " + cmdl
os.system(cmdl)
#p = subprocess.Popen(cmd)
