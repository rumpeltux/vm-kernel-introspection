# -*- coding: utf-8 -*-
# extension that allows to clone types
# i.e. create an identical copy of the type (except for id)

from c_types import *

def Type_clone(self):
    n          = self.__class__()
    n.__dict__ = dict(self.__dict__)
    n.id       = _new_id(self.type_list)

    n.type_list[n.id] = n
    return n

def Struct_clone(self, members=[]):
    "no auto-recursion. member names have to be specified explicitly"
    n = Type.clone(self)
    for i in range(0, len(n.members)):
      cur = self.type_list[self.members[i]]
      if cur.get_name() in members:
	new = cur.clone()
	self.members[i] = new.id
    return n

def Array_clone(self):
    """
    clones an array, but also clones it's base-type
    (only cloning the array does not seem to find a use-case)
    however this is inconsistent with the other clone-methods
    """
    n = Type.clone(self)
    self.base = self.get_base().clone().id

Type.clone   =   Type_clone
Struct.clone = Struct_clone
Array.clone  =  Array_clone

