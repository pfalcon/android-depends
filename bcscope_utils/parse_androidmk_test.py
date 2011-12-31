#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Test feasibility of generate cscope for android project
"""

import os
import androidmk_parser

modules = {}
def add_module_to_source(mod_name):
# do nothing if the module is already in modules collection
    if mod_name in modules:
        pass
    else:
        mod = all_modules.find_module(mod_name)
        if mod:
            modules[mod_name] = mod
            for dep in mod.depends:
                add_module_to_source(dep)

def print_modules():
    for (mod_name, mod) in modules.items():
        if not mod.src:
#            print mod_name + " src is null!!!"
            continue
        for src in mod.src.split():
            print os.path.join(mod.directory, src)

def generate_dependency_graph(dot_file_path):
    dot_file = open(dot_file_path, "w")
    dot_file.write("digraph {\n")
    for (mod_name, mod) in modules.items():
            dot_file.write("%s[label=\"%s\l%s\"]\n"%(mod.name, mod.name, mod.directory))
    for (mod_name, mod) in modules.items():
        for dep in mod.depends:
            dot_file.write("%s->%s\n"%(mod.name, dep))
    dot_file.write("}\n")
    dot_file.close()


import sys
all_modules = None
if __name__ == "__main__":
    dir_to_parse = os.path.curdir if len(sys.argv) < 2 else sys.argv[1]
    mk_files = androidmk_parser.find_android_mk(dir_to_parse)
    for mk_file in mk_files:
        all_modules = androidmk_parser.parse_makefile(mk_file, all_modules)
#    for (key,item) in all_modules.pool.items():
#        print key
#    module_to_find = "hstest"
#    add_module_to_source(module_to_find)

#    print_modules()
#    generate_dependency_graph("parse.dot")
    
#    print all_modules

