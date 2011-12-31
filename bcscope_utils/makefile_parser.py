#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import os

def function_basename(args, vp):
    args = args.split()
    result = ""
    for arg in args:
        basename = os.path.splitext(arg)
        result += basename[0] + " "
    return result.strip()

def function_dir(args, vp):
    args = args.split()
    result = ""
    for arg in args:
        dir_name = os.path.dirname(arg)
        if dir_name == "":
            dir_name = os.path.curdir
        result += dir_name + os.path.sep + " "
    return result.strip()

def function_notdir(args, vp):
    args = args.split()
    result = ""
    for arg in args:
        result += os.path.basename(arg) + " "
    return result.strip()

def function_addprefix(args, vp):
    args = args.split(",")
    prefix = args[0]
    names = args[1].split()
    result = ""
    if names:
        for name in names:
            result += prefix + name + " "
    return result.strip()

def function_addsuffix(args, vp):
    args = args.split(",")
    suffix = args[0]
    names = args[1].split()
    result = ""
    if names:
        for name in names:
            result += name + suffix + " "
    return result.strip()

class VariablePool(object):
    """A pool that manages variables in makefile
    """
    VAR_ASSIGNMENT_RX = re.compile("([a-zA-Z][a-zA-Z0-9_]*)\s*([:?\+]{0,1})=\s*(.*)")
#note: the $ sign followed by a single character also reference a variable
#   for example, $d reference variable d. Refer to gnu make manual.pdf section 6.1
    VAR_REFERENCE_RX = re.compile(r"\$[\({]([A-Za-z][A-Za-z0-9_]*)[}\)]")
    VAR_REFERENCE_RX = re.compile(r"\$(([\({]([A-Za-z][A-Za-z0-9_]*)[}\)])|([A-Za-z]\b))")
    FUNCTION_CALL_RX = re.compile(r"\$\(([a-z]+) ([a-z0-9_\-\.\\/]*)(,{0,1}\s*(.*)){0,1}\)")
# re.compile(r"\$(([\({]([A-Za-z][A-Za-z0-9_]*)[}\)])|([A-Za-z]\b))")
    MK_FUNCTIONS = {
            "basename" : function_basename,
            "notdir" : function_notdir,
            "dir" : function_dir,
            "addprefix" : function_addprefix,
            "addsuffix" : function_addsuffix
            }

    def __init__(self, makefile, make_functions = {}):
        self.immediate_variables = {}
        self.deferred_variables = {}
        self.makefile = makefile
        VariablePool.MK_FUNCTIONS.update(make_functions)

    def eval_expression(self, expression):
        expression = self.expand_var(expression)
        expression = self.expand_fun(expression)
        return expression
    
    def expand_fun(self, expression):
        match = self.FUNCTION_CALL_RX.search(expression)
        if match:
            fun_name = match.group(1)
            if fun_name == "call":
                fun_name = match.group(2)
                if fun_name in VariablePool.MK_FUNCTIONS:
                    func = VariablePool.MK_FUNCTIONS[fun_name]
                    expression = func(match.group(3) if len(match.groups()) > 3 \
                            else None, self)
            else:
                if fun_name in VariablePool.MK_FUNCTIONS:
                    func = VariablePool.MK_FUNCTIONS[fun_name]
                    arg = match.group(2)
                    if match.group(3):
                        arg += match.group(3)
                    expression = func(arg, self)
        return expression

    def expand_var(self, expression):
        match = self.VAR_REFERENCE_RX.search(expression)
        while match:
            var_name = match.group(3) if match.group(3) else match.group(4)
            var_value = self.immediate_variables[var_name] if \
                    var_name in self.immediate_variables else ""
            before = expression[:match.start()]
            after = expression[match.end():]
            expression = ""
            if before:
                expression += before
            if var_value:
                expression += var_value
            if after:
                expression += after

            match = self.VAR_REFERENCE_RX.search(expression)
        return expression

    def add_variable(self, rex_match):
        """Add a variable to the pool
        
        Args:
            rex_match: The match result of a string against 
            VariablePool.VAR_ASSIGNMENT_RX 

        Returns:
            The tuple (variable name, variable value) or None if the match failed

        """
        if not rex_match:
            return (None,None)
        var_name, var_type, var_value = rex_match.group(1, 2, 3)
        if var_type == ":":
            self.immediate_variables[var_name] = self.eval_expression(var_value)
        if var_type == "+":
            if var_name in self.immediate_variables:
#make appends new text preceded by a single space to a value
                self.immediate_variables[var_name] += " " \
                        + self.eval_expression(var_value)
            else:
                self.immediate_variables[var_name] = self.eval_expression(var_value)
        if var_type == "":
# a deferred variable, its expansion will not be done until required
# so, add it verbatimly now
            self.immediate_variables[var_name] = var_value
        return (var_name, var_value)

