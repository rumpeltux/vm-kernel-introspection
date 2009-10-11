# -*- coding: utf-8 -*-
from tools import *
import sys

if __name__=='__main__':
  if len(sys.argv) < 3:
	  print "usage: ", sys.argv[0], "<reference memory image> <altered memory image>"
	  sys.exit(1)
  
  refimg = sys.argv[1]
  newimg = sys.argv[2]

  types, names, addresses = init(refimg, parents=True, linked_lists=True)

  filesize = 4 * 1024**3 if newimg == "/dev/mem" else os.path.getsize(newimg)
  memory.map(newimg, filesize, filesize, 1)

  pgt = kernel_name('__ksymtab_init_level4_pgt')
  memory.set_init_level4_pgt(int(pgt.value.get_value()))

# recursionlimit at 1000 per default, but thats not enough
  sys.setrecursionlimit(8000)

#  temp = kernel_name('sys_call_table')
#  temp = kernel_name('cdrom_sysctl_header')
#  temp = kernel_name('sg_index_idr')
#  temp = temp.resolve()
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
	p = Memory(*v) 
	print "comparing: ", k
	total, faults = p.memcmp()
	symcounter += total
	errorcounter += faults
#	except MemoryAccessException, e:
#		print k, ": ", e
#		errorcounter += 1
#	except RecursingTypeException, e:
#		errorcounter += 1
#	except RuntimeError, e:
#		errorcounter += 1
#	except UserspaceVirtualAddressException, e:
#		errorcounter += 1
#	except PageNotPresent, e:
#		errorcounter += 1

  print "stats:"
  print "total symbols: %i, stayed same: %i, differring: %i, errors: %i" % (symcounter, samecounter, diffcounter, errorcounter)
  print "%f %% symbols changed or had errors" % (100.0 - (((samecounter + diffcounter) / (1.0 * symcounter)) * 100.0))
