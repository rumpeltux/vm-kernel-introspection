# -*- coding: utf-8 -*-
# initialisation functions for the type-parser
# s.t. Types will be created based on an information
# dictionary passed to the initialisation function
# each type has once been created this way

from c_types import *

def Type___init__(self, info, type_list=None):
    "initialize a new type. give it some info in a dictionary and a reference type_list"
    self.id = info['id']
    if "name" in info:
	self.name = ':' in info["name"] and info["name"].rsplit(':', 1)[1][1:] or info['name']
    if "type" in info:
	self.base = int(info["type"][1:-1], 16)
    self.type_list = type_list

def SizedType___init__(self, info, types=None):
    Type.__init__(self, info, types)
    if "byte_size" in info:
	if cmp(info["byte_size"][:2], '0x') == 0:
	#    print info, "\n"
	    self.size = int(info["byte_size"], 16)
	else:
	    self.size = int(info["byte_size"])

def Struct___init__(self, info, types=None):
    self.members = []
    SizedType.__init__(self, info, types)

def Array___init__(self, info, type_list):
    Type.__init__(self, info, type_list)

def Array_append(self, type):
    "append a Subrange-Type. copies the bound-value which is all we want to now"
    self.bound = type.bound

def BaseType___init__(self, info, type_list):
    SizedType.__init__(self, info, type_list)
    if "encoding" in info:
	self.encoding = int(info["encoding"][:2])

def Member___init__(self, info, type_list=None):
    self.offset = info.get('data_member_location', 0)
    Variable.__init__(self, info, type_list)

def Pointer___init__(self, info, type_list=None):
    BaseType.__init__(self, info, type_list)

def Subrange___init__(self, info, type_list):
    Type.__init__(self, info, type_list)
    if "upper_bound" in info:
	if info["upper_bound"] != "0x1ffff":
	    self.bound = int(info["upper_bound"], 10)

Type.__init__      =      Type___init__
SizedType.__init__ = SizedType___init__
Struct.__init__    =    Struct___init__
Array.__init__     =     Array___init__

Array.append       =     Array_append

BaseType.__init__  =  BaseType___init__
Member.__init__    =    Member___init__
Pointer.__init__   =   Pointer___init__

Subrange.__init__  =  Subrange___init__
