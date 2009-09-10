# -*- coding: utf-8 -*-
from tools import *
import sys

if __name__=='__main__':
  types, names, addresses = init("../ubuntu_memdump_before_terminal.dump")  

  memory.map("../ubuntu_memdump_after_terminal.dump", 600000000, 20000, 1)

  pgt = kernel_name('__ksymtab_init_level4_pgt')
  memory.set_init_level4_pgt(int(pgt.value.get_value()))

# recursionlimit at 1000 per default, but thats not enough
  sys.setrecursionlimit(8000)

#  temp = kernel_name('quota_genl_family')
#  print temp.memcmp()
#  sys.exit(0) 

  symcounter = 0
  samecounter = 0
  diffcounter = 0
  errorcounter = 0

  print "differing symbols:"
  for k,v in addresses.iteritems():
	if k == None:
		continue
	symcounter += 1
  	try:
		p = Memory(*v) 
		if not p.memcmp():
			print k
			diffcounter += 1
		else:
			samecounter += 1
	except MemoryAccessException, e:
#		print k, ": ", e
		errorcounter += 1
	except RecursingTypeException, e:
		errorcounter += 1
	except RuntimeError, e:
		errorcounter += 1
	except UserspaceVirtualAddressException, e:
		errorcounter += 1
	except PageNotPresent, e:
		errorcounter += 1
  print "stats:"
  print "total symbols: %i, stayed same: %i, differring: %i, errors: %i" % (symcounter, samecounter, diffcounter, errorcounter)
  print "%f %% symbols changed or had errors" % (100.0 - (((samecounter + diffcounter) / (1.0 * symcounter)) * 100.0))
