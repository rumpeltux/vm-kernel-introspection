# -*- coding: utf-8 -*-
from c_types import *

class String(Array):
    """
    represents a String in memory
    
    should be initialised with a Char-Array or Pointer to Char
    e.g.
	String(Array(type_of('unsigned char')))
	String(Pointer(type_of('char')))
    """
    def __init__(self, typ):
	self.type_list = typ.type_list
	self.base = typ.base
	self.bound = typ.bound if isinstance(typ, Array) else None
	#self.register()
	
    def takeover(self, typ):
	"replaces all occurances of typ in the global type list with this entry"
	self.id = typ.id
	self.type_list[id] = self
	
    def value(self, loc, depth=0):
	base = self.type_list[self.base]
	return base.get_value(loc, 10) # 10 == MEMORY_TYPE_NULLTERMINATED_STRING
	
	#out = ""
	#i = 0
	#while 1:
	  #typ, val = base.value(loc + base.size*i, depth+1)
	  #if type(val) != int or val > 255 or val == 0 or val < -128: break
	  #out += chr((val+256)%256)
	  #i += 1
	#return out

class NullTerminatedArray(Array):
    """
    Implements an Array type that is terminated by a NULL value
    either a NULL-Pointer if the elements are pointers,
    or 0 if the elements are other basic values
    
    The class provides only a custom iterator.
    High-level functions such as __len__ will not produce correct
    results, as the output is not dependent on the type, but on the
    type and memory location.
    """
    def __iter__(self, loc, depth=MAX_DEPTH):
	base = self.get_base()
	i = 0
	while 1:
	  member, member_loc = self.__getitem__(i, loc, depth)
	  
	  if isinstance(base, Pointer):
	    if base.get_pointer_address(member_loc) == 0:
	      break
	  elif isinstance(base, BasicType) and base.value(member_loc) == 0:
	    break
	    
	  yield member, member_loc
	  i += 1

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
    def get_pointer_value(self, loc, offset, image=0):
	if loc == 0:  raise NullPointerException(repr(self))
	ptr = resolve_pointer(loc + offset, image)
	# if we have a NULL pointer here then it is very likely
	# that we are at the beginning or end of a hlist_struct-like-list
	# or that there is no such list item, therefore throw a special 
	# EndOfListException
	if ptr == 0: raise EndOfListException(repr(self))
	#if ptr == 0: raise NullPointerException(repr(self))
	#print >>sys.stderr, "%x, %x" % (ptr, loc)
	return ptr
   
    def __getitem__(self, item, loc=None,  next_offset=None, image=0):
        if loc is None: return self.parent()
        if next_offset == None:
            next_offset = 0
        return self.parent(self.get_pointer_value(loc, self.entries[item], image) + next_offset)
    
    def __iter__(self, loc=None):
	for name,offset in self.entries.iteritems():
	  if loc is None:
	    yield self.parent()
	  else:
	    yield self.parent(self.get_pointer_value(loc,offset))

    def memcmp(self, loc, loc1, comparator, sympath=""):
	    next_offset = 0
	    if self.name == "children":
		next_offset = -16
	    try:	
		    if loc is None:
			    next_tuple = self.parent()
		    else:
			    next_tuple = self.parent(self.get_pointer_value(loc, self.entries["next"], 0) + next_offset)
		    if loc1 is None:
			    next1_tuple = self.parent()
		    else:
			    next1_tuple = self.parent(self.get_pointer_value(loc1, self.entries["next"], 1) + next_offset)
            except EndOfListException, e:
		    return True
	    comparator.enqueue(sympath + ".next", next_tuple[0], next_tuple[1], next1_tuple[1])

    def stringy(self, depth=0):
	return "\n".join(["\t%s → %s" % (name, self[name].__str__(depth+1).replace("\n", "\n\t"))
			  for name in self.entries])
    def value(self, loc, depth=MAX_DEPTH):
	# override this, since Struct.value will use the types name, which we suppress
	out = {}
	for key in self.entries:
	  out[key] = self[key]
	return out

class KernelSingleLinkedList(KernelLinkedList):
    entries = {'next': 0}

class KernelDoubleLinkedList(KernelLinkedList):
    entries = {'next': 0, 'prev': 8}
