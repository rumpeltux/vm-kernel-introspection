# -*- coding: utf-8 -*-
from c_types import *

def Type_clean(self):
  while self.base in self.type_list and self.type_list[self.base].id != self.base:
      self.base = self.type_list[self.base].id

def Struct_clean(self):
    Type.clean(self)
    for i in range(0, len(self.members)):
	while self.type_list[self.members[i]].id != self.members[i]:
	  self.members[i] = self.type_list[self.members[i]].id

Type.clean   = Type_clean
Struct.clean = Struct_clean

