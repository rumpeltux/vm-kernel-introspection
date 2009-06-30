# -*- coding: utf-8 -*-
from c_types import *
from c_types.user_types import *

from memory_manager import *
import memory, type_parser
memory.map("/dev/mem")
types, memory = type_parser.load(open("data.dumpc"))

names = {}
for k,v in types.iteritems():
  names[v.name] = k

addresses = {}
for k,v in memory.iteritems():
  addresses[types[v].name] = (k, types[v])

#some more cleanup i forgot
pat3= re.compile('DW_OP_plus_uconst: (\d+)')
for k,v in types.iteritems():
    if hasattr(v, "offset") and type(v.offset) != int:
        v.offset = int(pat3.search(v.offset).group(1))

type_of_address = lambda y: types[memory[y]]
cast = lambda memory, type: Memory(memory.get_loc(), type)
type_of = lambda name: types[names[name]]
pointer_to = lambda name: Pointer(type_of(name), types)
kernel_name = lambda name: Memory(*addresses[name])

def handle_array(array, member, struct, cls):
  """Replacing struct list_heads is difficult for Arrays
  So here we implement the special handling for this case.
  
  We create a pseudo member element for each array idx
  and then transform it into a KernelLinkedList that gets
  appended to the original data structure.
  Finally the obsolete array is removed from there"""
  
  idx = 0
  for entry,offset in array.__iter__(loc=0):
    pseudo_member = Type()
    pseudo_member.name = "%s_%d" % (member.name, idx)
    pseudo_member.offset = member.offset + offset
    new_element = cls(struct, pseudo_member)
    new_element.register()
    struct.append(new_element)
    idx += 1
  struct.members.remove(member.id)
  del types[member.id]

def prepare_list_heads():
  """kernel lists are a special thing and need special treatment
  this routine replaces all members of type struct list_head with
  an appropriate replacement that takes care handling these lists"""
  
  #TODO lists in struct -> array -> list_head… need a seperate type
  #     for each entry in array
  member_list = []
  arrad_handlers = []
  for k,v in types.iteritems():
    if isinstance(v, Struct):
      for member in v:
	lh = member.get_base()
	if lh and lh.name:
	  if lh.name == "list_head":
	    member_list.append((KernelDoubleLinkedList(v, member), member))
	if isinstance(lh, Array) and lh.get_base():
	  ar_lh = lh.get_base()
	  if ar_lh.name == "list_head":
	    arrad_handlers.append((lh, member, v, KernelDoubleLinkedList))

  for val in array_handlers:
    handle_array(*val)
	  
  for new_member, old_member in member_list:
      new_member.takeover(old_member)

prepare_list_heads()
print type_of('init_task')

def strings(phys_pos, filename):
  import memory
  f = open(filename, "w")
  while 1:
    s = memory.access(10, phys_pos)
    print >>f, "%08x\t%s" % (phys_pos, repr(s))
    phys_pos += len(s) + 1

def load_additional_symbols():
  pgt = kernel_name('__ksymtab_init_task') #first element
  syms = cast(pgt, Array(pgt.get_type()))
  i = 0
  try:
   while 1:
    name, value = str(cast(syms[i].name, Pointer(String(Array(type_of('unsigned char')))))), hex(syms[i].value)
    if not name in addresses and name in names: addresses[name] = (int(syms[i].value), type_of(name))
    i += 1
  except: pass

#load_additional_symbols()
#tracer = trace.Trace(ignoredirs=[sys.prefix, sys.exec_prefix], countfuncs=1, count=1, trace=0)

open("/tmp/init_task","w").write(str(kernel_name('init_task')))

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
