# -*- coding: utf-8 -*-
from c_types import *

Type.printed = 0

def Type___str__(self, depth=0):
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

def Struct_stringy(self, depth=0):
    "returns a string-representation of the members. close to c-struct designs"
    return "\n".join(
	["\t" + self.type_list[member].__str__(depth+1).replace("\n", "\n\t")
	    for member in self.members])

def Struct___str__(self, depth=0):
    return "struct %s {\n%s}" % (self.name, self.stringy(depth))

Struct.stringy = Struct_stringy
Type.__str__   =   Type___str__
Struct.__str__ = Struct___str__    