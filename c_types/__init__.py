# -*- coding: utf-8 -*-
import re
import memory

#at which depth level do we stop recursing:
MAX_DEPTH=5

#iters = 0

def _new_id(type_list):
    "Generate a new unique type id for the type list. random bruteforce approach"
    import random
    while 1:
      x = random.randint(0,2**31)
      if x not in type_list: return x

#def new_type(type_list, *args, **kwargs):
    #"hilfsfunktion zum erstellen des dicts für einen neuen typ"
    #kwargs['id'] = _new_id(type_list)
    #return kwargs

class Type:
    "BaseClass for all Types"
    name = None
    base = None

    def get_base(self):
	"""for convenient user access
returns a Type instance of this type’s base-type.
e.g. a Pointer to a Struct would have a base-type of Struct"""
	if self.base in self.type_list:
	      return self.type_list[self.base]
    def resolve(self, loc=None, depth=0):
	"""resolve the type

Some types are just intermediate Types that reference another Type
through the base property. E.g a Variable is a type on its own but
has a base-Type which is the Type of the Variable.

resolve() iterates until such a base-type is found."""
	return (self, loc)
    
    def value(self, loc, depth=0):
	"""assume memory at location loc is of our type

returns a tuple (type, value)
    where value may be a String representation for all but BaseTypes"""
        if depth > MAX_DEPTH: return "<unresolved @%x>" % loc
	if self.base:
	    type, val = self.type_list[self.base].value(loc, depth+1)
            return (type, "%s: " % self.name + str(val))
        return self.name and (self.name, 0) or ("[unknown:%x]" % self.id, 0)
#    def memcmp(self, loc, depth=0, seen=set([])):
    def memcmp(self, loc, depth=0, seen={}):
#	if (self, loc) in seen:
	try:
		if seen[self] != None:
			if loc in seen[self]:
				return True
	except KeyError, e:
		pass
#	if depth > MAX_DEPTH: return True
	if self.base:
#		seen.add((self, loc))
#		seen.add(self)
		try:
			if seen[self] != None:
				seen[self].add(loc)
		except KeyError, e:
			seen[self] = set([loc])
		return self.type_list[self.base].memcmp(loc, depth+1, seen)
	return True

    def register(self):
	"if this type is manually added, make it is also registered with a valid id in the global type register"
	self.id = _new_id(self.type_list)
	self.type_list[self.id] = self
    def get_name(self):
	"""returns a likely name for the type by iterating through the Types base-types
returns "void" if none is available"""
	name = self.name
	base = self.base
# is this an error? Or should it be fixed like i suggested in the comment
#	try:
		while not name and base:
		  name = self.type_list[self.base].name
		  if base == self.type_list[self.base].base: break
		  base = self.type_list[self.base].base
		return name and name or "void"
#	except KeyError, e:
#		return "void"

    def __repr__(self):
	return "<%s instance '%s'>" % (self.__class__, self.get_name())
	
    def bases(self):
	"iterate over all base-types"
	t = self
	while t.base and t.base in self.type_list:
	  t = self.type_list[t.base]
	  yield t

class SizedType(Type):
    "This is a Type with size-information associated"
    size = 0

class Struct(SizedType):
    "This type represents a C-structure. Its members usually have the type Member"
    def append(self, type):
	"adds a new member"
	self.members.append(type.id)
    
    def _value(self, loc, depth=0):
	"returns a c-like string representation of this struct’s values"
	#print "struct %s" % self.name, self.id, loc
	out = ""
        for real_member, member_loc in self.__iter__(loc):
	    member, member_loc = real_member.resolve(member_loc, depth+1)
	    if member_loc == 0: #prevent NullPointerExceptions
	      out += "\tvoid * %s = 0\n" % real_member.get_name()
	      continue
	    type, val = member.value(member_loc, depth+1)
	    type_str = (type != member.name) and "(%s)" % type or ""
            out += "\t%s%s %s = " % (member.name and member.name or "", type_str, real_member.name) + str(val).replace("\n","\n\t") + "\n"
        return out

    def value(self, loc, depth=0):
	"returns a c-like string representation of this struct including its values"
	if depth > MAX_DEPTH: return ("struct", "struct %s { … }" % self.get_name())
        return ("struct", "struct %s {\n%s}" % (self.get_name(), self._value(loc, depth)))

    def memcmp(self, loc, depth=0, seen={}):
        iseq = True
#	if (self, loc) in seen:
#	if self in seen:
#		return True
#	if self.name == "notifier_block":
#		global iters
#		iters+=1
#		if iters == 15:
#			print "15"
#		print "iter: %i" % (iters)
	try:
		if seen[self] != None:
			if loc in seen[self]:
				return True
	except KeyError, e:
		pass
        for real_member, member_loc in self.__iter__(loc):
            member, member_loc = real_member.resolve(member_loc, depth+1)
            if member_loc == 0:
                continue
#	    seen.add((self, loc))
#	    seen.add(self)
	    try:
		    if seen[self] != None:
			    seen[self].add(loc)
	    except KeyError, e:
		    seen[self] = set([loc])
            r = member.memcmp(member_loc, depth+1, seen)
            if not r:
                iseq = False
                break
        return iseq
        
    def __getitem__(self, item, loc=None):
        """returns the Type of this Structs member named item.
returns None if no such member exists

if loc is set, returns (member_type, member_location)"""
	for i in self.members:
	  if self.type_list[i].name == item:
	    item = self.type_list[i]
	    if loc is None:
	      return item
	    else:
	      return item, loc + item.offset
    def __iter__(self, loc=None):
	"iterate over all Members, if loc is set, yields (member_type, member_location)"
	for i in self.members:
	  if loc is None:
	    yield self.type_list[i]
	  else:
	    yield self.type_list[i], loc + self.type_list[i].offset

class Union(Struct):
    "This type represents a C-union which is basically a Struct where all members have the offset 0."
    def __str__(self, depth=0):
        return "union %s {\n%s}" % (self.get_name(), self.stringy(depth))
    def value(self, loc, depth=0):
	return ("union", "TODO union %s {\n%s}" % (self.get_name(), self._value(loc, depth)))
    def memcmp(self, loc, depth=0, seen={}):
	return True

class Array(Type):
    "Represents an Array. Including the upper bound"
    bound = None
    def __init__(self, info, bound=None):
	"Creates an Array with bound number of elements of Type info"
	self.base = info.id
	self.type_list = info.type_list
	self.bound = bound
	self.register()
	
    def __str__(self,depth=0):
        return "<Array[%s] %s>" % (self.bound, self.get_name())
	
    def value(self, loc, depth=0):
	"returns a c-like string-representation of an Array of this type located at location loc"
	if depth > MAX_DEPTH: return ("array", "…")
	
	ret = "%s {\n" % self.get_name()

	i = 0
	for member, member_loc in self.__iter__(loc, depth):
	  type, val = member.value(member_loc, depth+1)
	  ret += "\t[%d]: %s = %s\n" % (i, type, str(val).replace("\n", "\n\t"))
	  i += 1
	if self.bound is None: ret += "\t…\n"
	return ("array", ret + "}")

    def memcmp(self, loc, depth=0, seen={}):
#	    if (self, loc) in seen:
#	    if self in seen:
#		    return True
	    try:
		    if seen[self] != None:
			    if loc in seen[self]:
				    return True
	    except KeyError, e:
		    pass
#	    if depth > MAX_DEPTH: return True

	    iseq = True
	    for member, member_loc in self.__iter__(loc, depth):
#		    seen.add((self, loc))
#		    seen.add(self)
		    try: 
			    if seen[self] != None:
				    seen[self].add(loc)
		    except KeyError, e:
			    seen[self] = set([loc])
		    r = member.memcmp(member_loc, depth+1, seen)
		    if not r:
			    iseq = False
			    break
	    return iseq

    def get_element_size(self):
	"iterate on base-types and return the first one with size-information or None if no size seems to be known"
	#TODO cache this information for better performance
	base =  self.type_list[self.base]
	while not hasattr(base, "size"):
	    if not base.base:
		return None
	    base = self.type_list[base.base]
	  #try:
	  	#base = self.type_list[base.base]
	  #except KeyError:
		#print "array with no size"
		#raise RuntimeError
	return base.size
	
    def __getitem__(self, idx, loc=None, depth=0):
	if self.bound and (idx < 0 or idx >= self.bound):
	  raise IndexError("%d out of array bound %d (%s)" % (idx, self.bound, self))
	if loc is None:
	  return self.type_list[self.base]
	size = self.get_element_size()
	return self.type_list[self.base], loc + size * idx
	
    def __iter__(self, loc=None, depth=0):
	if self.bound is None:
	  yield self.__getitem__(0, loc, depth)
	  return
	for i in range(0, self.bound):
	  yield self.__getitem__(i, loc, depth)
	  
    def __len__(self):
	return self.bound+1 if self.bound else 1 #TODO 1 is not a good default, but __nonzero__ checks __len__ so we cannot return 0 or None

class Subrange(Type):
    "ArraySubrange-Type for use with Array. Holds bounds information"
    bound = None

class Function(Type):
    def __str__(self, depth=0):
        return "%s()" % self.get_name()
    def value(self, loc, depth=0):
	return ("function", "TODO func (%s())" % self.get_name())
    def memcmp(self, loc, depth=0, seen={}):
	return True

class MemoryAccessException(RuntimeError):
  pass
class NullPointerException(MemoryAccessException):
  pass

base_type_to_memory = {'int-5': 5, 'char-6': 1, 'None-7': 6, 'long unsigned int-7': 6, 'unsigned int-7': 4, 'long int-5': 7, 'short unsigned int-7': 2, 'long long int-5': 7, 'signed char-6': 1, 'unsigned char-8': 0, 'short int-5': 3, 'long long unsigned int-7': 6, '_Bool-2': 11, 'double-4': 8}

class BaseType(SizedType):
    """
    This is for real base-types like unsigned int
    
    encodings:
    2	(boolean)
    4	(float)
    5	(signed)
    6	(signed char)
    7	(unsigned)
    8	(unsigned char)
    
    10	(string)
    """
    encoding = 0

    @staticmethod
    def get_value(loc, mem_type=6, info=None): #unsigned long int
	"""uses the memory module to access physical memory
returns a representation based on mem_type
loc is a virtual address

may raise a MemoryAccessException"""
        if loc >= 0xffffffff80000000: #__START_KERNEL_map
	    loc -= 0xffffffff80000000
	elif loc >= 0xffff880000000000: #__PAGE_OFFSET
	    loc -= 0xffff880000000000
	else:
	    if loc == 0: raise NullPointerException(str(info))
	    raise MemoryAccessException("trying to access page 0x%x outside kernel memory (%s)" % (loc, info))
#        if loc == 0: raise NullPointerException(str(info))
#	physloc = memory.virt_to_phys(loc, 0)
	return memory.access(mem_type, loc, 0)
    
    @staticmethod
    def get_value1(loc, mem_type=6, info=None): #unsigned long int
        if loc >= 0xffffffff80000000: #__START_KERNEL_map
	    loc -= 0xffffffff80000000
	elif loc >= 0xffff880000000000: #__PAGE_OFFSET
	    loc -= 0xffff880000000000
	else:
	    if loc == 0: raise NullPointerException(str(info))
	    raise MemoryAccessException("trying to access page 0x%x outside kernel memory (%s)" % (loc, info))
#        if loc == 0: raise NullPointerException(str(info))
#	physloc = memory.virt_to_phys(loc, 1)
	return memory.access(mem_type, loc, 1)

    def value(self, loc, depth=0):
        #return self.get_value(loc, base_type_to_memory["%s-%d" % (self.name, self.encoding)])
	try:
	  return (self.name, self.get_value(loc, base_type_to_memory["%s-%d" % (self.name, self.encoding)]))
	except MemoryAccessException, e:
	  return (self.name, e)
    def memcmp(self, loc, depth=0, seen={}):
#	if (self, loc) in seen:
#	if self in seen:
#		return True
	try:
		if seen[self] != None:
			if loc in seen[self]:
				return True
	except:
		pass
	try:
		val1 = self.get_value(loc, base_type_to_memory["%s-%d" % (self.name, self.encoding)])
		val2 = self.get_value1(loc, base_type_to_memory["%s-%d" % (self.name, self.encoding)])
		return val1 == val2
	except MemoryAccessException, e:
		return (self.name, e)

class Enum(SizedType):
    enums = {}
    def append(self, enum):
        self.enums[enum.name] = enum.const
    #TODO...
class Enumerator(Type):
    def __init__(self, info, type_list):
        Type.__init__(self, info, type_list)
        self.const = int(info["const_value"])
    def __str__(self):
        return "%d (%s)" % (self.const, self.name)
            
class Variable(Type):
    def resolve(self, loc=None, depth=0):
	try:
		return self.type_list[self.base].resolve(loc, depth)
	except KeyError, e:
		print "another unhandled keyerror"
#		print self.type_list
#		print self.base
    def value(self, loc, depth=0):
	return self.type_list[self.base].value(loc, depth)
    def memcmp(self, loc, depth=0, seen={}):
#	if (self, loc) in seen:
#	if self in seen:
#		return True
	try:
		if seen[self] != None:
			if loc in seen[self]:
				return True
	except KeyError, e:
		pass
#	seen.add((self, loc))
#	seen.add(self)
	try:
		if seen[self] != None:
			seen[self].add(loc)
	except KeyError, e:
		seen[self] = set([loc])
	return self.type_list[self.base].memcmp(loc, depth, seen)

class Const(Variable):
    pass

class Member(Variable):
    "This is a StructureMember"
    offset = 0

class Pointer(BaseType):
    "Represents a Pointer to another type"
    def __init__(self, info):
	"Creates a Pointer pointing to memory of type info"
	self.base = info.id
	self.type_list = info.type_list
	self.register()
	
    def resolve(self, loc=None, depth=0):
	_loc = loc
	if _loc is not None:
	    try:
		_loc = self.get_value(loc, info=self) # unsigned long
	    except NullPointerException, e:
		return (self, loc)
	
	if self.base and _loc != 0:
	      return self.type_list[self.base].resolve(_loc, depth+1)
	else:
	      return (self, loc)
    def get_type_name(self):
	if self.base:
	  return "%s *" % self.type_list[self.base].get_name()
	return "void *"
    def value(self, loc, depth=0):
	if depth > MAX_DEPTH: return (self.get_type_name(), "…")
	
	ptr = self.get_value(loc) # unsigned long
	
	if self.base and ptr != 0:
	      return self.type_list[self.base].value(ptr, depth+1)
	else:
	      return (self.get_type_name(), ptr)
    def memcmp(self, loc, depth=0, seen={}):
#	if (self, loc) in seen:
#	if self in seen:
#		return True
	try:
		if seen[self] != None:
			if loc in seen[self]:
				return True
	except KeyError, e:
		pass
#        if depth > MAX_DEPTH: return True

	ptr = self.get_value(loc)

	if self.base and ptr != 0:
#		seen.add((self, loc))
#		seen.add(self)
		try: 
			if seen[self] != None:
				seen[self].add(loc)
		except KeyError, e:
			seen[self] = set([loc])
		try:
			return self.type_list[self.base].memcmp(ptr, depth+1, seen)
		except KeyError, e:
			print "another unhandled keyerror"
			raise RuntimeError("another unhandled keyerror")
			return True
	else:
		return True

class Typedef(Type):
    def resolve(self, loc, depth=0):
	if depth > 20: raise RuntimeError("recursing type...")
	return self.type_list[self.base].resolve(loc, depth+1)
    def value(self, loc, depth=0):
	return self.type_list[self.base].value(loc, depth+1)
    def memcmp(self, loc, depth=0, seen={}):
#	if (self, loc) in seen:
#	if self in seen:
#		return True
	try:
		if seen[self] != None:
			if loc in seen[self]:
				return True
	except KeyError, e:
		pass
#	seen.add((self, loc))
#	seen.add(self)
	try:
		if seen[self] != None:
			seen[self].add(loc)
	except:
		seen[self] = set([loc])
	return self.type_list[self.base].memcmp(loc, depth+1, seen)

resolve_pointer   = lambda loc: BaseType.get_value(loc)
