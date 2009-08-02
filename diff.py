# -*- coding: utf-8 -*-
import tools
from c_types import *
from c_types.user_types import *
from cPickle import load

from memory_manager import *
import memory, type_parser, bincmp, sys

memory.map("../ubuntu_memdump_before_terminal.dump", 20000, 0)
typesr, memoryl = type_parser.load(open("data.dumpc"))
#forward, backward = load(open("sysmap.dump"))

names, types, addresses = tools.init(parents=True)

cast = lambda memory, type: Memory(memory.get_loc(), type)
type_of = lambda name: types[names[name]]
pointer_to = lambda name: Pointer(type_of(name), types)
kernel_name = lambda name: Memory(*addresses[name])

if __name__=='__main__':
 # pgt = kernel_name('__ksymtab_init_level4_pgt')
 # pgt_t = cast(pgt.value, Pointer(Array(type_of('long unsigned int'), bound=512))) #eine möglichkeit
 # pgt4  = cast(pgt.value, Pointer(type_of('init_level4_pgt'))) #die andere möglichkeit
 # print pgt_t.get_value()[1]
  #dump_pagetables(pgt4, "/tmp/pages")
  memory.map("../ubuntu_memdump_before_terminal.dump", 20000, 0)
  memory.map("../ubuntu_memdump_after_terminal.dump", 20000, 1)

  pgt = kernel_name('__ksymtab_init_level4_pgt')
  memory.set_init_level4_pgt(int(pgt.value.get_value()))

# recursionlimit at 1000 per default, but thats not enough
  sys.setrecursionlimit(5000)

  temp = kernel_name('init_task')
  print temp.tasks.next.tasks.next
  sys.exit(0) 

  symcounter = 0
  samecounter = 0
  diffcounter = 0
  pagedcounter = 0
  othercounter = 0

#  for k,v in addresses.iteritems():
##	  if k == "_mpio_cache":
##		  continue
#	  try:
#		print k, ": ",
#		p = Memory(*v)
#		print p
#	  except UserspaceVirtualAddressException, e:
#		print "userspace address"
#	  except PageNotPresent, e:
#		print "page not present"
##	  except RuntimeError, e:
##		print "runtime error"
#
#  sys.exit(0)
#
  for k,v in addresses.iteritems():
	if k == None:
		continue
	symcounter += 1
  	try:
		print k, ": ",
		p = Memory(*v) 
		if not p.memcmp():
			print "false" 
			diffcounter += 1
		else:
			print "true"
			samecounter += 1
	except MemoryAccessException, e:
		print "MemoryAccessException: ", str(e)
		pagedcounter += 1
	except RecursingTypeException, e:
		print "recursing type"
		othercounter += 1
	except RuntimeError, e:
		print "runtime error"
		othercounter += 1
	except UserspaceVirtualAddressException, e:
		print "userspace address"
		othercounter += 1
	except PageNotPresent, e:
		print "page not present"
		othercounter += 1
#	except KeyError, e:
#		print "Key Error in symbol: ", k
#		othercounter += 1
#		sys.exit(0)

  print "stats:"
  print "symbols: %i, stayed same: %i, differring: %i, not handleable yet: %i" % (symcounter, samecounter, diffcounter, pagedcounter + othercounter)
  print "so we got a coverage of %f %% of the symbols" % ((samecounter + diffcounter) / symcounter)

#  print nr_cpu_ids
#  memory.map1("../ubuntu_memdump_after_terminal.dump", 20000)
 
#  memory.map("../ubuntu_memdump_before_terminal.dump", 20000)
#  print nr_cpu_ids.active_mm
#  memory.map("../ubuntu_memdump_after_terminal.dump", 20000)
#  print nr_cpu_ids.active_mm
  
#  	bdump = open("beforedump.txt", "w")
#	memory.map("../ubuntu_memdump_before_terminal.dump", 20000)
#	for k,v in addresses.iteritems():
#		p = kernel_name(k)
#		try:
#			strrep = str(p)	
#			bdump.write("%s\n" % strrep)
#		except:
#			continue
