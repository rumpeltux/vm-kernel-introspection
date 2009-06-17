# -*- coding: utf-8 -*-
from c_types import *
from memory_manager import *
import memory, type_parser
memory.map("/dev/mem")
types, memory = type_parser.load(open("data.dumpc"))

names = {}
for k,v in types.iteritems():
  names[v.name] = k

def addr(name):
  for k,v in memory.iteritems():
    if types[v].name == name: return (k,types[v])

#some more cleanup i forgot
pat3= re.compile('DW_OP_plus_uconst: (\d+)')
for k,v in types.iteritems():
    if hasattr(v, "offset") and type(v.offset) != int:
        v.offset = int(pat3.search(v.offset).group(1))

type_of_address = lambda y: types[memory[y]]
cast = lambda memory, type: Memory(memory.get_loc(), type)
type_of = lambda name: types[names[name]]
pointer_to = lambda name: Pointer(type_of(name), types)
kernel_name = lambda name: Memory(*addr(name))

def print_symtab(filename):
  f = open(filename, "w")
  pgt = kernel_name('__ksymtab_init_task') #first element
  syms = cast(pgt, Array(pgt.get_type()))
  i = 0
  try:
   while 1:
    name, value = str(cast(syms[i].name, Pointer(String(Array(type_of('unsigned char')))))), hex(syms[i].value)
    print >>f, name, value
    f.flush()
    i += 1
  except: pass
  f.close()

def dump_pagetables(pgt4, filename):
  f = open(filename, "w")
  page = lambda x: (x & ~0x8000000000000fff) + 0xffff880000000000
  is_null = lambda x: x.get_loc() == 0xffff880000000000
  loc  = lambda x: x.get_loc() - 0xffff880000000000
  for i in range(512):
    pud = Memory( page(pgt4[i].pgd.get_value()[1]), type_of('level3_kernel_pgt')) #raw addresses
    if not is_null(pud):
      print >>f, "  [%03d] --> %x" % (i, loc(pud))
      for j in range(512):
	pmd = Memory( page(pud[j].pud.get_value()[1]), type_of('level2_kernel_pgt'))
	if not is_null(pmd):
	  print >>f, "     [%03d] --> %x" % (j, loc(pmd))
	  for k in range(512):
	    pte = Memory( page(pmd[k].pmd.get_value()[1]), type_of('level2_kernel_pgt'))
	    if not is_null(pte) and pmd[k].pmd.get_value()[1] & 0x80 == 0: #skip LARGE PAGES for now
	      print >>f, "        [%03d] --> %x" % (k, loc(pte))
	      for l in range(512):
		if pte[l].pmd.get_value()[1] != 0:
		  print >>f, "           [%03d] --> %x" % (l, pte[l].pmd.get_value()[1])
  f.close()


if __name__=='__main__':
  pgt = kernel_name('__ksymtab_init_level4_pgt')
  pgt_t = cast(pgt.value, Pointer(Array(type_of('long unsigned int'), bound=512))) #eine möglichkeit
  pgt4  = cast(pgt.value, Pointer(type_of('init_level4_pgt'))) #die andere möglichkeit
  print pgt_t.get_value()[1]
  #dump_pagetables(pgt4, "/tmp/pages")

  init_mm = kernel_name('init_mm')
  init_mm.pgd.pgd
  print init_mm.pgd.pgd

  init_task = kernel_name('init_task')
  for i in init_task:
    print i.type.name

  print "out" + repr(init_task.usage)
  print "out" + repr(init_task.usage.counter)
  print init_task.usage.counter
  #print x(0xffffffff8091fdacL).value(0xffffffff8091fdacL)
