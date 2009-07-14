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
	
	return ('string', base.get_value(loc, 10)) # 10 == MEMORY_TYPE_NULLTERMINATED_STRING
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
    entries = {}

    def __init__(self, struct, member):
	"initialises the linked list entry"
	self.type_list = struct.type_list
	self._parent   = struct.id
	self.offset    = member.offset
	self.name      = member.name # "list_head(%s)" % struct.get_name()
    def takeover(self, member):
	"replaces all occurances of member in the global type list with this entry"
	if member.offset != self.offset:
	  raise Exception("cannot take over a foreign type!")
	self.id = member.id
	self.type_list[self.id] = self
    def parent(self, loc=None):
	if loc == 0: #NullPointerException
	  return Pointer(self.type_list[self._parent]), 0
	if not loc is None:
	  return self.type_list[self._parent], loc - self.offset
	return self.type_list[self._parent]
    def __getitem__(self, item, loc=None):
	if loc is None: return self.parent()
	return self.parent(resolve_pointer(loc + self.entries[item]))
    def __iter__(self, loc=None):
	for name,offset in self.entries.iteritems():
	  if loc is None:
	    yield self.parent()
	  else:
	    yield self.parent(resolve_pointer(loc+offset))
    def stringy(self, depth=0):
	return "\n".join(["\t%s → %s" % (name, self[name].__str__(depth+1).replace("\n", "\n\t"))
			  for name in self.entries])

class KernelSingleLinkedList(KernelLinkedList):
    entries = {'next': 0}

class KernelDoubleLinkedList(KernelLinkedList):
    entries = {'next': 0, 'prev': 8}
