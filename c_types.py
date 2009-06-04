# -*- coding: utf-8 -*-
import re
import memory

class Type:
    "BaseClass for all Types"
    name = None
    base = None
    lock = False
    depth = 0
    printed = False
    def __init__(self, info, type_list=None):
	"initialize a new type. give it some info in a dictionary and a reference type_list"
        self.id = info['id']
        if "name" in info:
            self.name = ':' in info["name"] and info["name"].rsplit(':', 1)[1][1:] or info['name']
        if "type" in info:
            self.base = int(info["type"][1:-1], 16)
        self.type_list = type_list

    def setDepth(self, depth):
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
    def get_base(self):
	"for convenient user access ;)"
	if self.base in self.type_list:
	      return self.type_list[self.base]
    def resolve(self, loc=None, depth=0):
	"resolve the type"
	return (self, loc)
    def __cmp__(self, other, depth=0):
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
    def value(self, loc, depth=0):
	"assume memory at location loc is of our type, output its value"
        if depth > 5: return "<unresolved @%x>" % loc
	print "type", self.name, self.id, loc
        if self.base:
	    type, val = self.type_list[self.base].value(loc, depth+1)
            return (type, "%s: " % self.name + str(val))
        return self.name and self.name or "[unknown:%x]" % self.id
    def clean(self):
        while self.base in self.type_list and self.type_list[self.base].id != self.base:
	    self.base = self.type_list[self.base].id
    def __str__(self, depth=0):
	"return a string representation of the type"
        out = self.name and self.name or "[unknown:%x]" % self.id
        if self.printed or self.lock or depth > 3: return "<%s…>" % out
        self.lock = True

        if self.base and self.type_list and self.base in self.type_list:
            try:
                out += " → " + self.type_list[self.base].__str__(depth+1)
            except RuntimeError, r:
                print out
                raise r
        self.lock = False
        #self.printed = True
        return "<"+out+">"
    def __repr__(self):
	return "<%s instance '%s'>" % (self.__class__, self.name)
class SizedType(Type):
    "This is a Type with size-information associated"
    size = 0
    def __init__(self, info, types=None):
        Type.__init__(self, info, types)
        if "byte_size" in info:
            if cmp(info["byte_size"][:2], '0x') == 0:
	    #    print info, "\n"
		self.size = int(info["byte_size"], 16)
	    else:
            	self.size = int(info["byte_size"])

class Struct(SizedType):
    "This type represents a C-structure"
    def __init__(self, info, types=None):
        self.members = []
        SizedType.__init__(self, info, types)
    def append(self, type):
        "adds a new member"
        self.members.append(type.id)
    def stringy(self, depth=0):
        return "\n".join(
            ["\t" + self.type_list[member].__str__(depth+1).replace("\n", "\n\t")
                for member in self.members])
    def setDepth(self, depth):
        if not Type.setDepth(self, depth): return False
        for member in self.members:
            try:
                self.type_list[member].setDepth(depth+1)
            except KeyError, k:
                print "key error:", self.id, self.members, self 
        return True
    def clean(self):
        Type.clean(self)
        for i in range(0, len(self.members)):
	    while self.type_list[self.members[i]].id != self.members[i]:
	      self.members[i] = self.type_list[self.members[i]].id
    def _value(self, loc, depth=0):
	print "struct %s" % self.name, self.id, loc
	out = ""
        for member in self.members:
            real_member = self.type_list[member]
	    offset = real_member.offset
	    member, member_loc = real_member.resolve(loc, depth+1)
	    print repr(member), repr(offset)
	    type, val = member.value(member_loc, depth+1)
            out += "\t%s(%s) %s = " % (member.name, type, real_member.name) + str(val).replace("\n","\n\t") + "\n"
        return out
    def value(self, loc, depth=0):
	if depth > 2: return ("struct", "struct %s { … }" % self.name)
        return ("struct", "struct %s {\n%s}" % (self.name, self._value(loc, depth)))
    def __cmp__(self, other, depth=0):
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
    def __str__(self, depth=0):
        return "struct %s {\n%s}" % (self.name, self.stringy(depth))

class Union(Struct):
    "This type represents a C-union structure."
    def __str__(self, depth=0):
        return "union %s {\n%s}" % (self.name, self.stringy(depth))
    def value(self, loc, depth=0):
	return ("union", "TODO union (%s)" % self.name)

class Array(Type):
    "Represents an Array. Including the upper bound"
    bound = None
    def append(self, type):
	"append a Subrange-Type. copies the bound-value which is all we want to now"
        self.bound = type.bound
    def __str__(self,depth=0):
        out = Type.__str__(self, depth)[1+len("[unknown:%x]"%self.id):]
        return "<Array[%s]" % self.bound + out
    def value(self, loc, depth=0):
	if not self.bound: return (None, "corrupted type: %d, %s" % (self.id, self))
	ret = "%s {\n" % self.name
	base =  self.type_list[self.base]
	
	#do not resolve. only look for size
	while not hasattr(base, "size"):
	  base = self.type_list[base.base]
	
	for i in range(self.bound):
	  type, val = base.value(loc + base.size*i, depth+1)
	  ret += "\t[%d]: %s = %s\n" % (i, type, str(val).replace("\n", "\n\t"))
	return ("array", ret + "}")

class Function(Type):
    def __str__(self, depth=0):
        return "%s()" % self.name
    def value(self, loc, depth=0):
	return ("function", "TODO func (%s())" % self.name)

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
    """
    encoding = 0
    def __init__(self, info, type_list):
        SizedType.__init__(self, info, type_list)
        if "encoding" in info:
            self.encoding = int(info["encoding"][:2])
    def get_value(self, loc, mem_type=6): #unsigned long int
	print "access at", hex(loc), hex( (loc-0xffffffff80000000) % (1 << 64))
	if loc < 0xffffffff80000000:
		raise RuntimeError("trying to access page 0x%x outside kernel memory (%s)" % (loc, self))
	loc -= 0xffffffff80000000 #__PAGE_OFFSET  
	return memory.access(mem_type, loc)
    def value(self, loc, depth=0):
        return (self.name, self.get_value(loc, base_type_to_memory["%s-%d" % (self.name, self.encoding)]))

class Enum(Type):
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
	return self.type_list[self.base].resolve(loc, depth+1)
    def value(self, loc, depth=0):
	return self.type_list[self.base].value(loc, depth+1)
class Const(Variable):
    pass

class Member(Variable):
    "This is a StructureMember"
    def __init__(self, info, type_list=None):
        self.offset = info.get('data_member_location', 0)
        Variable.__init__(self, info, type_list)

class Pointer(BaseType):
    def __init__(self, info, type_list):
	"info can be another type"
	if isinstance(info, Type):
	  self.base = info.id
	  self.type_list = type_list
	  return
	
        BaseType.__init__(self, info, type_list)
    def resolve(self, loc=None, depth=0):
	if loc is not None:
	    loc = self.get_value(loc) # unsigned long
	
	if self.base:
	      return self.type_list[self.base].resolve(loc, depth+1)
	else:
	      return self
    def value(self, loc, depth=0):
	ptr = self.get_value(loc) # unsigned long
	if self.base:
	      return self.type_list[self.base].value(ptr, depth+1)
	else:
	      return ("void *", ptr)
class Typedef(Type):
    def resolve(self, loc, depth=0):
	if depth > 20: raise RuntimeError("recursing type...")
	return self.type_list[self.base].resolve(loc, depth+1)
    def value(self, loc, depth=0):
	return self.type_list[self.base].value(loc, depth+1)

class Subrange(Type):
    "ArraySubrange-Type for use with Array. Holds bounds information"
    bound = None
    def __init__(self, info, type_list):
        Type.__init__(self, info, type_list)
        if "upper_bound" in info:
            if info["upper_bound"] != "0x1ffff":
                self.bound = int(info["upper_bound"], 10)