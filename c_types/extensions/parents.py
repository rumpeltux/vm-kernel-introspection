# -*- coding: utf-8 -*-
# parents extension
# provides functions to help enumerate all outgoing references
# from a Type

from c_types import *

Type.depth = 0

def Type_get_references(self):
    "returns all direct references to other types. used to initialsize the parents field"
    if self.base is not None:
	return [ self.type_list[self.base] ]
    return []

def Struct_get_references(self):
    "returns all direct references to other types. used to initialsize the parents field"
    l = Type.get_references(self)
    for i in self:
      l.append(i)
    return l

Type.get_references   = Type_get_references
Struct.get_references = Struct_get_references
#Arrays are handled using base attribute too

def enumerate_parents(types):
    "initialises and calculates the parent relationships"
    #initialise the lists
    for typ in types.values():
      typ.parents = []

    #append each typ to all of its references
    for typ in types.values():
      try:
	for ref in typ.get_references():
	  ref.parents.append(typ)
      except KeyError:
	pass