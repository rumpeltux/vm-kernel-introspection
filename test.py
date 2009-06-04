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
cast = lambda memory, type: Memory(memory.loc, type)
type_of = lambda name: types[names[name]]
pointer_to = lambda name: Pointer(type_of(name), types)
kernel_name = lambda name: Memory(*addr(name))

if __name__=='__main__':
  pgt = kernel_name('__ksymtab_init_level4_pgt')
  print pgt

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
