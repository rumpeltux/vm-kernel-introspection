# -*- coding: utf-8 -*-
import re, sys
from cPickle import dump, load
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

def cleanup(types):
    test = types.values()
    #for i in types:
    #    if i == types[i].id: test.append(types[i])
    print "elements:", len(test),
    test.sort()
    dups = 0
    for i in range(1, len(test)):
        if cmp(test[i-1], test[i]) == 0:
            types[test[i].id] = types[test[i-1].id]
            dups += 1
    del test
    print "removed:", dups
    #dump(types, open("data.dump","w"))
class Memory:
    def __init__(self, loc, type):
	self.loc = loc
	self.type = type
    def value(self):
	#type, loc = self.type.resolve(self.loc)
	#return type.value(loc)
	return self.type.value(self.loc)
    def __getattr__(self, key):
	this, loc = self.type.resolve(self.loc)
	print key, repr(this), loc, hex(loc)
	
	if not isinstance(this, Struct): return None
	for i in this.members:
	    t = this.type_list[i]
	    if t.name == key:
		return Memory(loc + t.offset, t)
	raise KeyError("%s has no attribute %s" % (repr(this), key))
    def __getitem__(self, idx):
	this, loc = self.type.resolve(self.loc)
	if not isinstance(this, Array): return None
	if idx > this.bound: raise IndexError("out of bounds")
	type = this.type_list[this.type.base]
	size_type = type
	while not hasattr(size_type, "size"):
	  size_type = this.type_list[size_type.base]
	return Memory(loc + idx * size_type.size, size_type)
    def __iter__(self):
	this, loc = self.type.resolve(self.loc)
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
	return "<Memory %s @0x%x>" % (repr(self.type), self.loc)

def read_types(f):
    """
    read file f which is the output of `objdump -g kernel' and parse its structures.
    returns two dictionaries: (memory, types)
    memory holds memory locations
    types contains all type information.
    both need to be cleaned up in order to reduce memory footprint, because they include
    many redundant information
    """
    
    #regular expression patterns
    pat = re.compile('(<\d>)?<([0-9a-f]+)>:?\s*(.+?)\s*: (.+)')
    pat2= re.compile('DW_(AT|TAG)_(\w+)')
    pat3= re.compile('DW_OP_addr: ([a-f0-9]+)')
    info = {}
    types = {}
    baseType = None
    
    #which Class corresponds to which tag-value
    classes = {'structure_type': Struct, 'union_type': Union, 'member': Member, 'array_type': Array, 'subroutine_type': Function, 'enumeration_type': Enum, 'enumerator': Enumerator, 'pointer_type': Pointer, 'subrange_type': Subrange, 'variable': Variable, 'base_type': BaseType, 'typedef': Typedef}
    #which tag-values to ignore
    ignores = {'formal_parameter': 1, 'subprogram': 1, 'inlined_subroutine': 1, 'lexical_block': 1}
    i = 0
    memory = {}
    skippy = False
    stack = [None for i in range(10)]
    this = None
    
    # speedup hack
    # dupcheck = {}
    
    for line in f:
        i += 1
        if i % 1000 == 0:
            sys.stderr.write("%d\t%d\r" % (i,len(types)))
        if i % 900000 == 0:
            cleanup(types) #takes long, but needed to reduce ram-usage
        
	ret = pat.search(line.strip())
        if not ret:
            #print "dbg: no-match: %s" % line,
            continue
        
        head, pos, a, b = ret.groups() #match each line
        pos = int(pos, 16) #binary position in file used to index types
        if head: #subtype or alike
            tag = pat2.search(b).group(2)
            if info and not skippy: #handle collected info of last type
            
                if info['id'] in types: #if this type is already registered…
                    print "should not happen"
                    this = types[info['id']]
                else:
                    #select the right class based on tag
                    cls = classes.get(info['tag'], Type)
                    this = cls(info, types)
                    
                #save type for its id (id=bin_loc)
		# speedup hack
		#tmprepr = this.id
		#try:
	#		dupcheck[tmprepr]
	#	except KeyError: 
	#		dupcheck[tmprepr] = 1;
               	types[info['id']] = this
                
                #save the location
                if 'location' in info:
                    location = pat3.search(info['location'])
                    if location:
                        memory[int(location.group(1), 16)] = info['id']
                
                stack[info['head']] = this
                if info['head'] > 1:
                    #print "append", this, "to", baseType
                    if hasattr(stack[info['head']-1], "append"):
                        stack[info['head']-1].append(this)
                    #else:
                        #print baseType, "wont let me append a", info['tag']
            
                #end handling previous type
            
            #init new type
            info = {'id': pos, 'tag': tag, 'head': int(head[1:-1])}
            if info['head'] == 1: #reset any skip commands
                skippy = False
            #print this, info
            if tag in ignores:  #skip the whole section
                #print tag, info, this
                skippy = True

        #append new information to existing type
        ret = pat2.search(a)
        if ret:
            info[ret.group(2)] = b

    return types, memory

def create_initial_dump(in_file, out_file):
    ret = read_types(open(in_file))
    print "dumping"
    dump(ret, open(out_file, "w"))
    return ret

def clean_initial_dump(name, ret=None):
    "removes any ids, that are not needed for task-fullfillment"
    print "load dump"
    if ret:
      types, memory = ret
      print "skipped"
    else:
      types, memory = load(open(name))
      #memory, types = load(open(name))

    print "validate model"
    try:
      for id, typ in types.iteritems():
	if types[typ.id].id != typ.id:
	    print "weirdo", typ.id, repr(types[typ.id]), types[typ.id]
	    types[typ.id] = typ
    except AttributeError, e:
        print "at-error", id, repr(typ), typ
            
    print "removing duplicates",
    tmp = []
    try:
      for id, typ in types.iteritems():
	  if typ.id == id:
            tmp.append(typ)
    except AttributeError, e:
	  print id, repr(typ), typ, e

    print len(tmp), "elements"
    tmp.sort()
    dups = 0
    for i in range(1, len(tmp)):
        if cmp(tmp[i-1], tmp[i]) == 0:
            types[tmp[i].id] = types[tmp[i-1].id]
            dups += 1
    print "removed", dups, "duplicates"
    
    print "validate model"
    tmp = set()
    for id, typ in types.iteritems():
        if types[typ.id].id != typ.id:
            tmp.add(typ.id)
    print len(tmp), "errors in model…"
    
    print "clean types"
    #clean all known types
    dups = 0
    for id, typ in types.iteritems():
        if typ.id == id:
            typ.clean()
	    dups += 1
    print dups, "types cleaned"
    
    print "clean memory"
    for loc,id in memory.iteritems():
        while types[id].id != id:
            memory[loc] = types[id].id
            id = types[id].id
    
    print "clean references"
    #remove now unreferenced types
    dups = 0
    for id in types.keys():
        if types[id].id != id:
            del types[id]
	    dups += 1
    print dups, "obselete types removed"

    print "saving dump"
    dump((types, memory), open(name+"c", "w"))
    return types, memory

def print_symbols(types, memory):
    for loc, mem in memory.iteritems():
        if types[mem].depth == 0:
            print types[mem].value(loc)
        else:
            print "skipping", types[mem].name, types[mem].depth

def playground((types, memory)):
    import type_parser
    t = type_parser.Type({'id': 0})
    for id, typ in types.iteritems():
        if typ.__class__ == t.__class__ and not typ.base and typ.name:
            print typ.name
        
if __name__ == "__main__":
    from os import popen
    DUMP_FILENAME = "data.dump"
    
    def load_and_init():
        types, memory = load(open(DUMP_FILENAME+"c"))
	for i in memory:
            types[memory[i]].setDepth(0)
        return types, memory
    if len(sys.argv) < 2:
        print "%s (init|clean|print|state|load)" % sys.argv[0]
	sys.exit(0)
    if sys.argv[1] == "init":
        clean_initial_dump(DUMP_FILENAME, create_initial_dump(sys.argv[2], DUMP_FILENAME))
    elif sys.argv[1] == "clean":
        types, memory = clean_initial_dump(DUMP_FILENAME)
    elif sys.argv[1] == "print":
        print_symbols(load_and_init())
    elif sys.argv[1] == "state":
        print_system_state(load_and_init())
    elif sys.argv[1] == "play":
        playground(load_and_init())
    

