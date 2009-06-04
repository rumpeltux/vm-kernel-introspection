# -*- coding: utf-8 -*-
from c_types import *
class Memory:
    "Memory Manager. Holds typed and addressed information, resolves structures and makes members accessible"
    def __init__(self, loc, type):
	self.__loc = loc
	self.__type = type
    def get_type(self):
	return self.__type
    def __value(self):
	#type, loc = self.type.resolve(self.loc)
	#return type.value(loc)
	return self.__type.value(self.__loc)
    def __getattr__(self, key):
	this, loc = self.__type.resolve(self.__loc)
	print key, repr(this), loc, hex(loc)
	
	if not isinstance(this, Struct): return None
	for i in this.members:
	    t = this.type_list[i]
	    if t.name == key:
		return Memory(loc + t.offset, t)
	raise KeyError("%s has no attribute %s" % (repr(this), key))
    def __getitem__(self, idx):
	this, loc = self.type.resolve(self.__loc)
	if not isinstance(this, Array): return None
	if idx > this.bound: raise IndexError("out of bounds")
	type = this.type_list[this.type.base]
	size_type = type
	while not hasattr(size_type, "size"):
	  size_type = this.type_list[size_type.base]
	return Memory(loc + idx * size_type.size, size_type)
    def __iter__(self):
	this, loc = self.type.resolve(self.__loc)
	if isinstance(this, Struct):
	    for member in this.members:
		t = this.type_list[member]
		yield Memory(loc + t.offset, t)
	elif isinstance(this, Array):
	    type = this.type_list[this.type.base]
	    size_type = type
	    while not hasattr(size_type, "size"):
		size_type = this.type_list[size_type.base]
	    for idx in range(this.bound):
		yield Memory(loc + idx * size_type.size, size_type)
    def __str__(self):
	return str(self.value())
    def __repr__(self):
	return "<Memory %s @0x%x>" % (repr(self.__type), self.__loc)
