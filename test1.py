# -*- coding: utf-8 -*-
from c_types import *
from memory_manager import *
import memory, type_parser, re
memory.map("../ubuntu_memdump.dump", 2000000)
types, memoryl = type_parser.load(open("data.dumpc"))

names = {}
for k,v in types.iteritems():
  names[v.name] = k

def addr(name):
  for k,v in memoryl.iteritems():
    if types[v].name == name: return (k,types[v])

#some more cleanup i forgot
pat3= re.compile('DW_OP_plus_uconst: (\d+)')
for k,v in types.iteritems():
    if hasattr(v, "offset") and type(v.offset) != int:
        v.offset = int(pat3.search(v.offset).group(1))

type_of_address = lambda y: types[memoryl[y]]
cast = lambda memory, type: Memory(memory.loc, type)
type_of = lambda name: types[names[name]]
pointer_to = lambda name: Pointer(type_of(name), types)
kernel_name = lambda name: Memory(*addr(name))

def grep_System_map(symname):
	sympat = re.compile('([a-f0-9]+) (.) (\w+)')
	mapfile = "System.map"
	systemmap = open(mapfile, 'r')
	for line in systemmap:
		ret = sympat.search(line.strip())
		if not ret:
			continue
		addr, t, name = ret.groups()
		if name == symname:
			return int(addr, 16)
	raise RuntimeError("symbol %s not found in %s" % (symname, mapfile))

if __name__=='__main__':
    code_resource = kernel_name('code_resource')
    
    kernel_code_start = code_resource.start.get_value()[1]
    __START_KERNEL_map = 0xffffffff80000000

# from System.map maybe has to be readout too ...
    #_text = 0xffffffff80200000
    _text = grep_System_map('_text')

    phys_base = kernel_code_start - (_text - __START_KERNEL_map)
    print hex(phys_base)

# maybe a simpler way to get all the kernel variables ??
    init_level4_pgt = grep_System_map('init_level4_pgt')
    pgt = kernel_name('__ksymtab_init_level4_pgt')
    print hex(pgt.value.get_value()[1])
    print hex(init_level4_pgt) # the same in my test environment
