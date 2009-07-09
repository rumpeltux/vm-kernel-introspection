# -*- coding: utf-8 -*-
from tools import *

init() 
  #"/dev/mem"
  #"../ubuntu_memdump_before_terminal.dump"

if __name__=='__main__':
  #ksize = kernel_name('ksize')  
  #print ksize
  #pgt = kernel_name('__ksymtab_init_level4_pgt')
  #pgt_t = cast(pgt.value, Pointer(Array(type_of('long unsigned int'), bound=512))) #eine möglichkeit
  #pgt4  = cast(pgt.value, Pointer(type_of('init_level4_pgt'))) #die andere möglichkeit
  #print pgt_t.get_value()[1]
  ##dump_pagetables(pgt4, "/tmp/pages")
#
#  init_mm = kernel_name('init_mm')
#  init_mm.pgd.pgd
#  print init_mm.pgd.pgd
#
#  init_task = kernel_name('init_task')
#  for i in init_task:
#    print i.type.name
#
#  print "out" + repr(init_task.usage)
#  print "out" + repr(init_task.usage.counter)
#  print init_task.usage.counter
#  #print x(0xffffffff8091fdacL).value(0xffffffff8091fdacL)
