# -*- coding: utf-8 -*-
# extension to compare instances of types on a
# debug-symbol level (not for memory), because
# the kernel object dump will contain many duplicates
#
# comparism is recursive because name and other attributes
# may not be sufficient to be sure the type is equal or not

from c_types import *

def Type___cmp__(self, other, depth=0):
      "compare this to another type. returns 0 if (we think that) the types are the same"
      ret = cmp(self.id, other.id)
      if ret == 0 or depth>2: return 0 #quick exit, if we know (or feel) we are the same…
      
      ret = cmp(self.name, other.name)
      if ret != 0: return ret #not same name?

      ret = cmp(self.__class__, other.__class__)
      if ret != 0: return ret #not the same type-class?
      
      if hasattr(self, "size") and hasattr(other, "size"):
	  ret = cmp(self.size, other.size)
      if ret != 0: return ret #not same size?
      
      #if there is a lock we entered a circle and should assume both types
      #are the same.
      #TODO: check if this is really true or if there are some border conditions
      if self.lock or other.lock: return 0
      self.lock = True
      
      #recursively check base types
      if self.base in self.type_list and other.base in self.type_list:
	  ret = self.type_list[self.base].__cmp__(self.type_list[other.base], depth+1)
      else:
	  ret = cmp(self.base, other.base)
      
      self.lock = False

      return ret
def Struct___cmp__(self, other, depth=0):
      ret = cmp(self.id, other.id)
      if ret == 0 or depth>2: return 0 #quick exit, if we know (or feel) we are the same…
      ret = Type.__cmp__(self, other, depth)
      if ret != 0: return ret
      if not isinstance(other, Struct):
	  return -1
      self.lock = True
      ret = cmp(len(self.members), len(other.members))
      if ret == 0:
	  for i in range(0, len(self.members)):
	      ret = self.type_list[self.members[i]].__cmp__(self.type_list[other.members[i]], depth+1)
	      if ret != 0: break
      self.lock = False
      return ret

def Member___cmp__(self, other, depth=0):
      "Make sure, the offset is accounted for"
      ret = cmp(self.id, other.id)
      if ret == 0 or depth>2: return 0 #quick exit, if we know (or feel) we are the same…
      ret = Type.__cmp__(self, other, depth)
      if ret != 0: return ret
      if not hasattr(other, "offset"): return -1
      return cmp(self.offset, other.offset)


Type.__cmp__   = Type___cmp__
Struct.__cmp__ = Struct___cmp__
Member.__cmp__ = Member___cmp__

