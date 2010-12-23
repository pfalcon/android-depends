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

DEFAULT_PRODUCT_NAME="generic"

def find_debugger(android_src_root, version=""):
    """
    find android debugger
    return the latest version of all debuggers if version is not specified
    return empty string on failure
    """
    debugger_name = "arm-eabi-gdb"
    debugger_path = ""
    if sys.platform.startswith("linux"):
        debugger_pattern = ".+linux.+" + version + ".+" + debugger_name
        p = subprocess.Popen(["find", android_src_root+os.sep+"prebuilt", "-iregex", debugger_pattern], stdout=subprocess.PIPE)
        p.wait()
    output = p.stdout.readlines()
    if len(output) > 0:
        debugger_path = output[len(output)-1].rstrip()
    return debugger_path

def find_pid_of_process(process_name):
    """
    find pid of target process
    return "0" on failure
    """
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
    return pid.rstrip()

def attach_gdbserver(port, pid):
    """
    attach gdbserver to target process
    """
    cmd = ["adb", "shell", "gdbserver", ":"+port, "--attach", pid]
#    pr = subprocess.Popen(cmd)#, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    os.system("adb shell gdbserver :" + port + " --attach " + pid + " &")

def find_process_symbol(android_src_root, process_name, product_name=DEFAULT_PRODUCT_NAME):
    """
    find symbol file for process
    return empty string on failure
    """
    symbol_root = "%s/out/target/product/%s/symbols/"%(android_src_root, product_name)
    process_symbol = ""
    if sys.platform.startswith("linux"):
        process_symbol_pattern = ".+" + process_name 
        p = subprocess.Popen(["find", symbol_root, "-iregex", process_symbol_pattern], stdout=subprocess.PIPE)
        p.wait()
    output = p.stdout.readlines()
    if(len(output) > 0):
        process_symbol = output[0].rstrip()
    return process_symbol 

def start_gdb_client(android_src_root, debugger, process, product_name=DEFAULT_PRODUCT_NAME, debugger_wrapper_type = "gdb"):
    lib_symbol_root = "%s/out/target/product/%s/symbols/system/lib"%(android_src_root, product_name)
    cmdl = '%s %s -ex "set solib-search-path %s"'%(debugger, process, lib_symbol_root)
    # run gdb under cgdb 
    if debugger_wrapper_type == "cgdb":
        cmdl = "cgdb -d " + cmdl
    os.system(cmdl)

if __name__ == "__main__":
    debugger_wrappers = ["gdb", "cgdb", "ddd"]
    KEY_ANDROID_SRC_ROOT = "ANDROID_SRC_ROOT"
    default_android_src_root = ""
    if os.environ.has_key(KEY_ANDROID_SRC_ROOT):
        default_android_src_root = os.environ[KEY_ANDROID_SRC_ROOT]

    # parse command line options
    opt_parser = OptionParser(version = "%prog " + __VERSION__, 
                description = "wrapper on android gdb",
                usage = "%prog [options] process_name")
    opt_parser.add_option("", "--android-src-root", dest="android_src_root", default=default_android_src_root, 
            help="root of android source tree, can be set via "+KEY_ANDROID_SRC_ROOT+" environment variable")
    opt_parser.add_option("-d", "--debugger-wrapper", dest="debugger_wrapper", default=debugger_wrappers[0], 
            help="wrappers on gdb, e.g., cgdb, ddd")
    opt_parser.add_option("-p", "--port", dest="gdb_port", default="7890", 
            help="port used for gdbserver, [default: %default]")
    (cmdline_options, args) = opt_parser.parse_args()
    if len(args) < 1:
        print "must specify process name"
        sys.exit(-1)
    process_name = args[0]
    if cmdline_options.android_src_root == None or cmdline_options.android_src_root == "":
        print "android-src-root must be set"
        sys.exit(-1)

    debugger = find_debugger(cmdline_options.android_src_root)
    pid = find_pid_of_process(process_name)
    process_symbol = find_process_symbol(cmdline_options.android_src_root, process_name)
    attach_gdbserver(cmdline_options.gdb_port, pid)
    start_gdb_client(cmdline_options.android_src_root, debugger, process_symbol, debugger_wrapper_type=cmdline_options.debugger_wrapper)
