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
      elif not hasattr(self, "size") and not hasattr(other, "size"):
	  pass
      else: #one has size, the other not
	  ret = 1 if hasattr(self, "size") else -1
      if ret != 0: return ret #not same size?
      
      #if there is a lock in both we entered a circle in both and
      #should assume both types are the same.
      #  however there might be cases in which this is not true
      #  (e.g. seemingly equal types with selfreferences…)
      if self.lock and other.lock: return 0

      #if just one has a lock: this is a difference
      if self.lock or other.lock: return 1 if self.lock else -1

      self.lock = True
      
      #recursively check base types
      if self.base in self.type_list and other.base in self.type_list:
	  ret = self.type_list[self.base].__cmp__(self.type_list[other.base], depth+1)
      else: #compare ids if one of the types is not yet known
	  ret = cmp(self.base, other.base)
      
      self.lock = False
      return ret

def Struct___cmp__(self, other, depth=0):
      ret = cmp(self.id, other.id)
      if ret == 0 or depth>2: return 0 #quick exit, if we know (or feel) we are the same…

      ret = Type.__cmp__(self, other, depth) #checks for common stuff.
      if ret != 0: return ret

      #class equality is already checked by Type.__cmp__
      #if not isinstance(other, Struct): return -1

      #if both have the lock we need to exit
      if self.lock and other.lock: return 0
      #if just one has the lock, Type.__cmp__ handled that already

      #lock to avoid recursion
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

      #superfluous because class-check is made in Type.__cmp__
      #if not hasattr(other, "offset"): return -1
      return cmp(self.offset, other.offset)

# Type.__cmp__ handles comparism for SizedTypes also. So this can be skipped here

Type.__cmp__   = Type___cmp__
Struct.__cmp__ = Struct___cmp__
Member.__cmp__ = Member___cmp__

