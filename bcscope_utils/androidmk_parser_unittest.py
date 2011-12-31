#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""unittest for parse.py
"""

__author__ = 'rx.wen218@gmail.com'

import unittest
from androidmk_parser import *
from makefile_parser import VariablePool
import re

class VariablePoolTest(unittest.TestCase):
    def setUp(self):
        pass

    def test_func_my_dir(self):
        vp = AndroidMKVariablePool("Android.mk")
        self.assertEqual(".", vp.eval_expression("$(call my-dir)"))
        vp = AndroidMKVariablePool("../Android.mk")
        self.assertEqual("..", vp.eval_expression("$(call my-dir)"))
        vp = AndroidMKVariablePool("subdir/Android.mk")
        self.assertEqual("subdir", vp.eval_expression("$(call my-dir)"))
        vp = AndroidMKVariablePool("/home/Android.mk")
        self.assertEqual("/home", vp.eval_expression("$(call my-dir)"))

    def test_variable(self):
        vp = VariablePool("Android.mk")
# add a non-assignment line
        (var_name, var_value) = \
            vp.add_variable(VariablePool.VAR_ASSIGNMENT_RX.match("aaalisa"))
        self.assertEqual(0, len(vp.immediate_variables))
        self.assertEqual(None, var_name)
        self.assertEqual(None, var_value)
# add new variable
        (var_name, var_value) = \
            vp.add_variable(VariablePool.VAR_ASSIGNMENT_RX.match("aaa:=lisa"))
        self.assertEqual(1, len(vp.immediate_variables))
        self.assertEqual("lisa", vp.immediate_variables["aaa"])
        self.assertEqual("aaa", var_name)
        self.assertEqual("lisa", var_value)
# override variable
        vp.add_variable(VariablePool.VAR_ASSIGNMENT_RX.match("aaa:=raymond"))
        self.assertEqual(1, len(vp.immediate_variables))
        self.assertEqual("raymond", vp.immediate_variables["aaa"])
# update variable
        vp.add_variable(VariablePool.VAR_ASSIGNMENT_RX.match("aaa+=raymond"))
        self.assertEqual(1, len(vp.immediate_variables))
        self.assertEqual("raymond raymond", vp.immediate_variables["aaa"])
# add deferred variable
        vp.add_variable(VariablePool.VAR_ASSIGNMENT_RX.match("bbb=$(aaa)"))
        self.assertEqual(2, len(vp.immediate_variables))
        self.assertEqual("$(aaa)", vp.immediate_variables["bbb"])
        self.assertEqual("raymond raymond", vp.eval_expression("$(bbb)"))
# a non-variable is evaled to itself
        self.assertEqual("raymond", vp.eval_expression("raymond"))
# variable should be expanded recursively
        vp.add_variable(VariablePool.VAR_ASSIGNMENT_RX.match("ccc := $(bbb)"))
        self.assertEqual(3, len(vp.immediate_variables))
        self.assertEqual(vp.eval_expression("$(ccc)"), vp.eval_expression("$(aaa)"))
# a vairable doesn't exist should be expanded to empty string
        self.assertEqual("", vp.eval_expression("${non_variable}"))
# a single letter variable
        vp.add_variable(VariablePool.VAR_ASSIGNMENT_RX.match("d:=single/letter"))
        self.assertEqual(4, len(vp.immediate_variables))
        self.assertEqual(vp.eval_expression("$(d)"), vp.eval_expression("single/letter"))
# single letter variables can be referenced this way
        self.assertEqual(vp.eval_expression("$d"), vp.eval_expression("single/letter"))

    def test_func_notdir(self):
        vp = AndroidMKVariablePool("Android.mk")
        self.assertEqual("/home/a", vp.eval_expression("$(basename /home/a.cpp)"))
        self.assertEqual("/home/a", vp.eval_expression("$(basename /home/a.cpp )"))
        self.assertEqual("/home/a b", vp.eval_expression("$(basename /home/a.cpp b.c)"))
        self.assertEqual("/home/a /home/b", vp.eval_expression("$(basename /home/a.cpp /home/b.c)"))

    def test_func_notdir(self):
        vp = AndroidMKVariablePool("Android.mk")
        self.assertEqual("a.cpp", vp.eval_expression("$(notdir /home/a.cpp)"))
        self.assertEqual("a.cpp", vp.eval_expression("$(notdir /home/a.cpp )"))
        self.assertEqual("a.cpp b.c", vp.eval_expression("$(notdir /home/a.cpp b.c)"))
        self.assertEqual("a.cpp b.c", vp.eval_expression("$(notdir /home/a.cpp /home/b.c)"))

    def test_func_dir(self):
        vp = AndroidMKVariablePool("Android.mk")
        self.assertEqual("/home/", vp.eval_expression("$(dir /home/a.cpp)"))
        self.assertEqual("/home/", vp.eval_expression("$(dir /home/a.cpp )"))
        self.assertEqual("/home/ ./", vp.eval_expression("$(dir /home/a.cpp b.c)"))
        self.assertEqual("/home/ /home/", vp.eval_expression("$(dir /home/a.cpp /home/b.c)"))

    def test_func_addprefix(self):
        vp = AndroidMKVariablePool("Android.mk")
        self.assertEqual("src/bbb", vp.eval_expression("$(addprefix src/, bbb)"))
        self.assertEqual("src\\bbb", vp.eval_expression("$(addprefix src\\, bbb)"))
        self.assertEqual("aaabbb", vp.eval_expression("$(addprefix aaa, bbb )"))
        self.assertEqual("aaabbb aaaccc", vp.eval_expression("$(addprefix aaa, bbb ccc)"))
        vp.add_variable(VariablePool.VAR_ASSIGNMENT_RX.match("aaa:=lisa"))
        self.assertEqual("lisabbb lisaccc", vp.eval_expression("$(addprefix $(aaa), bbb ccc)"))
        vp.add_variable(VariablePool.VAR_ASSIGNMENT_RX.match("d:=rrr"))
        self.assertEqual("rrrlisa rrrccc", vp.eval_expression("$(addprefix $d, $(aaa) ccc)"))

    def test_func_addsuffix(self):
        vp = AndroidMKVariablePool("Android.mk")
        self.assertEqual("bbbaaa", vp.eval_expression("$(addsuffix aaa, bbb)"))
        self.assertEqual("bbbaaa", vp.eval_expression("$(addsuffix aaa, bbb )"))
        self.assertEqual("bbb.c ccc.c", vp.eval_expression("$(addsuffix .c, bbb ccc)"))
        vp.add_variable(VariablePool.VAR_ASSIGNMENT_RX.match("d:=.cpp"))
        self.assertEqual("ccc.cpp", vp.eval_expression("$(addsuffix $d, ccc)"))

if __name__ == "__main__":
    unittest.main()
