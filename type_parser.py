# -*- coding: utf-8 -*-
import re, sys
from cPickle import dump, load

class Type:
    name = None
    base = None
    lock = False
    depth = 0
    printed = False
    def __init__(self, info, type_list=None):
        self.id = info['id']
        if "name" in info:
            self.name = ':' in info["name"] and info["name"].rsplit(':', 1)[1][1:] or info['name']
        if "type" in info:
            self.base = int(info["type"][1:-1], 16)
        self.type_list = type_list
        #print id, info
#        if self.name:
#            print "new type: %s" % self
    def setDepth(self, depth):
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
    def __cmp__(self, other, depth=0):
        ret = cmp(self.id, other.id)
        if ret == 0 or depth>2: return 0 #quick exit, if we know (or feel) we are the same…
        ret = cmp(self.name, other.name)
        if ret != 0: return ret
        if hasattr(self, "size") and hasattr(other, "size"):
            ret = cmp(self.size, other.size)
        if ret != 0: return ret
        if self.lock or other.lock: return 0
        self.lock = True
        if self.base in self.type_list and other.base in self.type_list:
            ret = self.type_list[self.base].__cmp__(self.type_list[other.base], depth+1)
        else:
            ret = cmp(self.base, other.base)
        self.lock = False
        return ret
    def value(self, loc, depth=0):
        if depth > 2: return "<unresolved @%x>" % loc
        if self.base:
            return self.types[self.base].value(loc, depth+1)
        return self.name and self.name or "[unknown:%x]" % self.id
    def clean(self):
        if self.base in self.type_list:
            self.base = self.type_list[self.base].id
    def __str__(self, depth=0):
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
class SizedType(Type):
    size = 0
    def __init__(self, info, types=None):
        Type.__init__(self, info, types)
        if "byte_size" in info:
            self.size = int(info["byte_size"])

class Member(SizedType):
    def __init__(self, info, type_list=None):
        self.offset = info.get('data_member_location', 0)
        SizedType.__init__(self, info, type_list)

class Struct(SizedType):
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
            self.members[i] = self.type_list[self.members[i]].id
    def _value(self, loc, depth=0):
        out = ""
        for member in self.members:
            member = self.type_list[member]
            out += member.value(loc + member.offset, depth+1).replace("\n","\n\t") + "\n"
        return out
    def value(self, loc, depth=0):
        return "struct %s {\n%s}" % (self.name, self._value(depth))
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
    def __str__(self, depth=0):
        return "union %s {\n%s}" % (self.name, self.stringy(depth))

class Array(Type):
    bound = None
    def append(self, type):
        self.bound = type.bound
    def __str__(self,depth=0):
        out = Type.__str__(self, depth)[1+len("[unknown:%x]"%self.id):]
        return "<Array[%s]" % self.bound + out

class Function(Type):
    def __str__(self, depth=0):
        return "%s()" % self.name

class BaseType(SizedType):
    encoding = 0
    def __init__(self, info, type_list):
        SizedType.__init__(self, info, type_list)
        if "encoding" in info:
            self.encoding = int(info["encoding"][:2])
class Enum(Type):
    enums = {}
    def append(self, enum):
        self.enums[enum.name] = enum.const

class Enumerator(Type):
    def __init__(self, info, type_list):
        Type.__init__(self, info, type_list)
        self.const = int(info["const_value"])
    def __str__(self):
        return "%d (%s)" % (self.const, self.name)
            
class Variable(Type):
    pass
class Pointer(SizedType):
    pass
class Subrange(Type):
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

def read_types(f):
    pat = re.compile('(<\d>)?<([0-9a-f]+)>:?\s*(.+?)\s*: (.+)')
    pat2= re.compile('DW_(AT|TAG)_(\w+)')
    pat3= re.compile('DW_OP_addr: ([a-f0-9]+)')
    info = {}
    types = {}
    baseType = None
    classes = {'structure_type': Struct, 'union_type': Union, 'member': Member, 'array_type': Array, 'subroutine_type': Function, 'enumeration_type': Enum, 'enumerator': Enumerator, 'pointer_type': Pointer, 'subrange_type': Subrange, 'variable': Variable}
    ignores = {'formal_parameter': 1, 'subprogram': 1, 'inlined_subroutine': 1, 'lexical_block': 1}
    i = 0
    memory = {}
    skippy = False
    stack = [None for i in range(10)]
    this = None
    for line in f:
        i += 1
        if i % 1000 == 0:
            sys.stderr.write("%d\t%d\r" % (i,len(types)))
        if i % 10000000 == 0:
            cleanup(types) #takes long, but needed to reduce ram-usage
        #if i > 5000000: break
        
        ret = pat.search(line.strip())
        if not ret:
            #print "dbg: no-match: %s" % line,
            continue
        
        head, pos, a, b = ret.groups()
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
        
    return memory, types

def create_initial_dump(in_file, out_file):
    ret = read_types(open(in_file))
    dump(ret, open(out_file, "w"))

def clean_initial_dump(name):
    "removes any ids, that are not needed for task-fullfillment"
    print "load dump"
    types, memory = load(open(name))

    print "validate model"
    for id, typ in types.iteritems():
        try:
            if types[typ.id].id != typ.id:
                types[typ.id] = typ
        except AttributeError, e:
            print id, repr(typ), typ
            
    print "removing duplicates"
    tmp = []
    for id, typ in types.iteritems():
        if typ.id == id:
            tmp.append(id)
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
    for id, typ in types.iteritems():
        if typ.id == id:
            typ.clean()
    
    print "clean memory"
    for loc,id in memory.iteritems():
        if types[id].id != id:
            memory[loc] = types[id].id
    
    print "clean references"
    #remove now unreferenced types
    for id in types.keys():
        if types[id].id != id:
            del types[id]

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
    if sys.argv[1] == "init":
        create_initial_dump(sys.argv[2], DUMP_FILENAME)
    elif sys.argv[1] == "clean":
        types, memory = clean_initial_dump(DUMP_FILENAME)
    elif sys.argv[1] == "print":
        print_symbols(load_and_init())
    elif sys.argv[1] == "state":
        print_system_state(load_and_init())
    elif sys.argv[1] == "play":
        playground(load_and_init())
    

