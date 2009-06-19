# -*- coding: utf-8 -*-
from c_types import *

class String(Array):
    """Represents a String in Memory. Should be initialised with a Char-Array
e.g.: String(Array(type_of('unsigned char')))"""
    def __init__(self, typ):
	self.type_list = typ.type_list
	self.base = typ.base
	self.bound = typ.bound
	self.register()
    def value(self, loc, depth=0):
	out = ""
	base = self.type_list[self.base]
	
	return ('string', base.get_value(loc, 10))
	i = 0
	while 1:
	  typ, val = base.value(loc + base.size*i, depth+1)
	  if type(val) != int or val > 255 or val == 0 or val < -128: break
	  out += chr((val+256)%256)
	  i += 1
	return ('string', out)


class KernelLinkedList(Struct):
    "Implements the linked lists which the kernel uses using preprocessor macros"
    
    parent = None
    offset = 0
    def __init__(self, struct, member):
	self.type_list = struct.type_list
	self.parent    = struct.id
	self.offset    = member.offset
	self.register()
    def parent(self, loc=None):
	if loc:
	  return self.type_list[self.parent], loc - offset
	return self.type_list[self.parent]
    def __getitem__(self, item, loc=None):
	if loc is None: return self.parent()
	
	if item == "next": return self.parent(resolve_pointer(loc))
	if item == "prev": return self.parent(resolve_pointer(loc+8))
	if item == "top": return self.parent(loc)
    def __iter__(self, loc=None):
	if loc == None:
	  yield self.parent
	  yield self.parent
	yield self.parent(resolve_pointer(loc))  #next
	yield self.parent(resolve_pointer(loc+8))#prev
    def value(self, loc, depth=0):
	ret = ""
	for n, t, l in [
	    ("next", self.parent(resolve_pointer(loc))),
	    ("prev", self.parent(resolve_pointer(loc+8)))
	    ]:
	  typ, val = t.value(l)
	  ret += "\t%s = %s\n" % (i, str(val).replace("\n", "\n\t"))
	return ("struct", "struct list_head {\n%s}" % ret)

#long_pointer_type = Pointer(BaseType({'id': 0, 'byte_size': 8, 'encoding': '07'}))
#resolve_pointer   = lambda loc: long_pointer_type.value(loc)
#__all__ = [Type]