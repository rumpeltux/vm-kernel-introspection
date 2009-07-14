# -*- coding: utf-8 -*-
# extensions to replace base-references of duplicate
# types to the one representant

from c_types import *

def Type_clean(self):
  while self.base in self.type_list and self.type_list[self.base].id != self.base:
      self.base = self.type_list[self.base].id
  if self.base is not None and not self.base in self.type_list:
      print "error: base %x missing" % self.base

def Struct_clean(self):
    Type.clean(self)
    for i in range(0, len(self.members)):
	while self.type_list[self.members[i]].id != self.members[i]:
	  self.members[i] = self.type_list[self.members[i]].id

Type.clean   = Type_clean
Struct.clean = Struct_clean

