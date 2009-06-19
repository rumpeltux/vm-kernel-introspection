# -*- coding: utf-8 -*-
from c_types import *

Type.depth = 0

def Type_setDepth(self, depth):
    "recursively enumerate structure depths. prevents cycles using the lock"
    ret = False
    if self.lock: return False
    self.lock = True
    if depth > self.depth:
	self.depth = depth
	ret = True
    if self.base in self.type_list:
	self.type_list[self.base].setDepth(depth+1)
    self.lock = False
    return ret

def Struct_setDepth(self, depth):
      if not Type.setDepth(self, depth): return False
      for member in self.members:
	  try:
	      self.type_list[member].setDepth(depth+1)
	  except KeyError, k:
	      print "key error:", self.id, self.members, self 
      return True

Type.setDepth   = Type_setDepth
Struct.setDepth = Struct_setDepth
