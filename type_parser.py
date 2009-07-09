# -*- coding: utf-8 -*-
import re, sys
from cPickle import dump, load
from c_types import *

def cleanup(types):
    """sorts all types using their __cmp__ function which does a deep inspection.
    
    removes duplicates by references to the first occurence of an equivalent type"""
    test = []
    for id,typ in types.iteritems():
      if id == typ.id: test.append(typ)
    #test = types.values()
    #for i in types:
    #    if i == types[i].id: test.append(types[i])
    print "\nnow sorting…",
    print "elements:", len(test)
    test.sort()
    print "sort complete, cleaning up"
    dups = 0
    groups = {}
    representant = None
    for i in range(1, len(test)):
        if cmp(test[i - 1], test[i]) == 0:
	    if representant == None: representant = test[i-1].id
	    groups[test[i].id] = representant
	    types[test[i].id] = types[test[i - 1].id]
            dups += 1
	else:
	    representant = None
    del test
    print "removed:", dups
    for id,typ in types.iteritems():
      if typ.id in groups:
	types[id] = types[groups[typ.id]]
    print "index updated"

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
    pat2 = re.compile('DW_(AT|TAG)_(\w+)')
    pat3 = re.compile('DW_OP_addr: ([a-f0-9]+)')
    pat4 = re.compile('DW_OP_plus_uconst: (\d+)')
    info = {}
    types = {}
    baseType = None
    
    #which Class corresponds to which tag-value
    classes = {'structure_type': Struct, 'union_type': Union, 'member': Member, 'array_type': Array, 'subroutine_type': Function, 'enumeration_type': Enum, 'enumerator': Enumerator, 'pointer_type': Pointer, 'subrange_type': Subrange, 'variable': Variable, 'base_type': BaseType, 'typedef': Typedef, 'const_type': Const}
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
            sys.stderr.write("%d\t%d\r" % (i, len(types)))
        if i % 5000000 == 0:
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

		if 'data_member_location' in info:
		    info['data_member_location'] = int(pat4.search(info['data_member_location']).group(1))

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
                    if hasattr(stack[info['head'] - 1], "append"):
                        stack[info['head'] - 1].append(this)
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
    types, memory = read_types(open(in_file))
    cleanup(types)
    dump((types, memory), open(out_file, "w"))
    return types, memory

def clean_initial_dump(name, ret=None):
    "removes any ids, that are not needed for task-fullfillment"
    print "load dump"
    if ret:
      types, memory = ret
      print "skipped"
    else:
      types, memory = load(open(name))
      #memory, types = load(open(name))

    weirdos = 0
    print "validate model"
    try:
      for id, typ in types.iteritems():
	if types[typ.id].id != typ.id:
	    print "weirdo", typ.id #, repr(types[typ.id]), types[typ.id]
	    types[typ.id] = typ
	    weirdos += 1
    except AttributeError, e:
        print "at-error", id, repr(typ), typ
    if weirdos != 0: print "validation failed:", weirdos, "errors"

    print "removing duplicates (should be 0!)"
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
        if cmp(tmp[i - 1], tmp[i]) == 0:
            types[tmp[i].id] = types[tmp[i - 1].id]
            dups += 1
    print "removed", dups, "duplicates"
    
    print "validate model"
    tmp = set()
    for id, typ in types.iteritems():
        if types[typ.id].id != typ.id:
            tmp.add(typ.id)
    print len(tmp), "errors in model… (MUST be 0)"
    
    print "clean types"
    #clean all known types
    dups = 0
    for id, typ in types.iteritems():
        if typ.id == id: #clean only real types. e.g. each type only once
            typ.clean()
	    dups += 1
    print dups, "types cleaned"
    
    print "clean memory"
    for loc, id in memory.iteritems():
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
    dump((types, memory), open(name + "c", "w"))
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

def dump_sysmap(dumpfile, sysmap):
    mapfile = open(sysmap, 'r')
    sympat = re.compile('([a-f0-9]+) (.) (\w+)')
    forward = {}
    backward = {}
    for line in mapfile:
        ret = sympat.search(line.strip())
        if not ret:
            continue
        addr, t, name = ret.groups()
        intaddr = int(addr, 16)
        forward[name] = intaddr
        backward[intaddr] = name
    dump((forward, backward), open(dumpfile, 'w'))

def test():
    class SimpleType:
      def __init__(self, id, order):
	self.id=id
	self.order=order
      def __cmp__(self, b):
	return cmp(self.order, b.order)
      def __repr__(self):
	return "<%d : %d>" % (self.id, self.order)
    ST = SimpleType
    types = {}
    
    def init_types(data):
      for i in data:
	types[i.id] = i
	
    init_types([ST(1,1), ST(2,2), ST(3,3), ST(4,2)])
    cleanup(types)
    print types
    #should be {1: <1 : 1>, 2: <2 : 2>, 3: <3 : 3>, 4: <2 : 2>}
        
    init_types([ST(8,2)])
    cleanup(types)
    print types
    #should be {8: <8 : 2>, 1: <1 : 1>, 2: <8 : 2>, 3: <3 : 3>, 4: <8 : 2>}
if __name__ == "__main__":
    from os import popen
    from c_types.extensions import clean, compare, string, init
    
    DUMP_FILENAME = "data.dump"
    SYSMAP_DUMP = "sysmap.dump"
    
    def load_and_init():
        types, memory = load(open(DUMP_FILENAME + "c"))
	for i in memory:
            types[memory[i]].setDepth(0)
        return types, memory
    if len(sys.argv) < 2:
        print "%s (init|clean|print|state|load|readmap)" % sys.argv[0]
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
    elif sys.argv[1] == "readmap":
        dump_sysmap(SYSMAP_DUMP, sys.argv[2])
    elif sys.argv[1] == "test":
	test()

