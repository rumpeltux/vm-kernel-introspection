# -*- coding: utf-8 -*-
# extensions to return string representation of in c-like syntax
# mainly interesting while coding/debugging

from c_types import *

Type.printed = 0

def Type_crep(self, loc, depth=0):
    """
    assume memory at location loc is of our type

    returns a tuple (type, value)
    where value may be a String representation for all but BaseTypes
    """
    if depth > MAX_DEPTH: return ("<unresolved @%x>" % loc, None)
    if self.base is not None:
	type, val = self.type_list[self.base].value(loc, depth+1)
	return (type, "%s: " % self.name + str(val))
    return self.name and (self.name, None) or ("[unknown:%x]" % self.id, None)

def Void_value(self, loc, depth=0):
    return ("void", None)

def Struct_crep(self, loc, depth=0):
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

def Struct_crep(self, loc, depth=0):
    "returns a c-like string representation of this struct including its values"
    if depth > MAX_DEPTH: return ("struct", "struct %s { … }" % self.get_name())
    return ("struct", "struct %s {\n%s}" % (self.get_name(), self._value(loc, depth)))

def Union_crep(self, loc, depth=0):
    return ("union", "TODO union %s {\n%s}" % (self.get_name(), self._value(loc, depth)))

def Array_crep(self, loc, depth=0):
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

    def Function_crep(self, loc, depth=0):
	return ("function", "TODO func (%s())" % self.get_name())

    def BaseType_crep(self, loc, depth=0):
        #return self.get_value(loc, base_type_to_memory["%s-%d" % (self.name, self.encoding)])
	try:
#	  if loc == 0xffffe200006e5a78:
#		  print "puller!", self.name
	  return (self.name, self.get_value(loc, base_type_to_memory["%s-%d" % (self.name, self.encoding)]))
	except MemoryAccessException, e:
	  return (self.name, e)

    def Pointer_crep(self, loc, depth=0):
	if depth > MAX_DEPTH: return (self.get_type_name(), "…")

	ptr = self.get_value(loc) # unsigned long
	
	if self.base is not None and ptr != 0:
	      return self.type_list[self.base].value(ptr, depth+1)
	else:
	      return (self.get_type_name(), ptr)
Struct.stringy = Struct_stringy
Type.__str__   =   Type___str__
Struct.__str__ = Struct___str__    