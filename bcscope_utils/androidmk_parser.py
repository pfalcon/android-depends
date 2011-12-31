#!/usr/bin/env python
# -*- coding: utf-8 -*-

import makefile_parser
import os
import re

def function_all_java_files_under(args, vp):
    result = []
    args_rx = re.compile(",\s*(.*)")
    match = args_rx.match(args)
    if match:
        directory = match.group(1) 
        android_mk_dir = os.path.dirname(vp.makefile)
        for src_dir in directory.strip().split():
            for (root, dirnames, filenames) in \
                    os.walk(os.path.join(android_mk_dir, src_dir)):
                for file_name in filenames:
                    extens = os.path.splitext(file_name)
                    if extens and extens[1].lower() == ".java":
                        result.append(os.path.join(\
                                os.path.relpath(root, android_mk_dir), \
                                file_name))
    str = ""
    for item in result:
        str += " " + item
    return str

def function_all_subdir_java_files(args, vp):
    return function_all_java_files_under(", .", vp)

def function_my_dir(args, vp):
    my_dir = os.path.dirname(vp.makefile)
    return os.path.curdir if my_dir == "" else my_dir

def find_root():
    """ Find root directory of android source tree

    Returns:
        A string represents the root directory relative to current dir
        Return None if the root directory can't be determined
    """

    curdir = os.path.curdir
    fs_root = "/"
    # Do as build/envsetup.sh does
    # if this files exists, we're at root
    root_clue = "build/core/envsetup.mk"
    found = False
    while not found and not os.path.samefile(fs_root, curdir):
        if os.path.exists(os.path.join(curdir, root_clue)):
            found = True
            break
        curdir = os.path.join(os.path.pardir, curdir)
    return curdir if found else None

def find_android_mk(dirpath):
    """ Find all Android.mk under dirpath

    Returns:
        A list of pathes to Android.mk files under dirpath
    """

    result = []
    for (root, dirnames, filenames) in os.walk(dirpath):
        for file_name in filenames:
            if file_name.upper() == "ANDROID.MK":
                result.append(os.path.join(root, file_name))
    return result

class Module(object):
    """Module class represents a module definition in Android.mk

    A module is defined by a LOCAL_MODULE 
    """
    def __init__(self):
        self.name = None
        self.depends = []
        self.src = None
        self.directory = None
    
    def add_depend_module(self, module):
        """Add a module that current module depends on

        A dependent module is defined by a LOCAL_STATIC_LIBRARIES 
        or LOCAL_SHARED_LIBRARIES

        Args:
            module: the module dependent on

        """
        self.depends.append(module)

    def __str__(self):
        result = self.name
        for module in self.depends:
            result += " " + module.name + " : " + module.src
        return result

class ModulePool(object):
    """ModulePool class manages all module have seen so far
    """
    def __init__(self):
        self.pool = {}

    def add_module(self, module):
        """Add a module to the pool

        Args:
            module: the module to be added

        """
        if module.name not in self.pool:
            self.pool[module.name] = module

    def find_module(self, name):
        """Find a module matches given name

        Args:
            name: the name of the module to find

        """
        if name in self.pool:
            return self.pool[name]
        else:
            return None

    def __str__(self):
        result = ""
        for (k, v) in sorted(self.pool.items()):
            if v.src:
                result += v.name + " : " + v.directory + "\n"\
                        + v.src + " \n"
            else:
                print v.name + " is None !!!!!!!!!!!!!!!!!!!!!!!!!!:"
                print v.depends
        return result

class AndroidMKVariablePool(makefile_parser.VariablePool):
    """
    """

    def __init__(self, makefile):
        android_mk_functions = {
                "all-java-files-under": function_all_java_files_under,
                "all-subdir-java-files": function_all_subdir_java_files,
                "my-dir": function_my_dir
#all-harmony-test-java-files-under
                }
        super(AndroidMKVariablePool, self).__init__(makefile, android_mk_functions)

def parse_makefile(fn, existing_modules=None):
    """Parse a Makefile-style file.

    A dictionary containing name/value pairs is returned.  If an
    optional dictionary is passed in as the second argument, it is
    used instead of a new dictionary.
    """
    from distutils.text_file import TextFile
    fp = TextFile(fn, strip_comments=1, skip_blanks=1, join_lines=1)

    local_modules = ModulePool()
    if existing_modules:
        local_modules.pool.update(existing_modules.pool) 
    variable_pool = AndroidMKVariablePool(fn)

    current_module = None

    while 1:
        line = fp.readline()
        if line is None:  # eof
            break
        if line.upper() == "include $(CLEAR_VARS)".upper():
            current_module = None

        match = makefile_parser.VariablePool.VAR_ASSIGNMENT_RX.match(line)
        if match:
            (var_name, var_value) = variable_pool.add_variable(match)
            if not current_module:
                current_module = Module()
                current_module.directory = os.path.dirname(fn)

            if var_name == "LOCAL_MODULE":
                var_value = variable_pool.eval_expression(var_value)
                temp_module = local_modules.find_module(var_value)
                if temp_module and temp_module != current_module:
                    temp_module.src = current_module.src
                    temp_module.depends = current_module.depends
                    current_module = temp_module
                current_module.name = var_value
                local_modules.add_module(current_module)

            if var_name == "LOCAL_SRC_FILES":
                if current_module:
                    current_module.src = var_value

            if var_name == "LOCAL_STATIC_LIBRARIES" or \
                    var_name == "LOCAL_SHARED_LIBRARIES":
                if current_module:
                    for i in var_value.split():
                        current_module.depends.append(i)

    fp.close()

    # update values in modules
    for (key,item) in local_modules.pool.items():
#v.src may be None, for example, libext module in iptables/extensions/Android.mk
        value = item.src
        if not value:
            continue
        value = variable_pool.eval_expression(value)
        item.src = value
        number = len(item.depends)
        index = 0
        while index < number:
            value = item.depends[index]
            value = variable_pool.eval_expression(value)
            items = value.split()
            if len(items) > 0:
                item.depends[index] = items[0]
                item.depends.extend(items[1:])
                number += len(items) - 1
                index += 1
            else:
                item.depends.pop(index)
                number -= 1

    return local_modules
