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

# example: for only comparing one toplevel symbol
#  temp = kernel_name('sys_call_table')
#  print temp.memcmp()
#  sys.exit(0)

  symcounter = 0
  samecounter = 0
  diffcounter = 0
  errorcounter = 0

  print "differing symbols:"
  for k,v in addresses.iteritems():
	  # ignore all the "evil" symbols (quick and dirty hack)
	  # most of them have a "sock" struct inside, which
	  # may cause some problems
	if k == "idiagnl" or k == "scsi_nl_sock" or k == "fib6_rules_ops_template" or k == "audit_skb_hold_queue" or k == "genl_sock" or k == "audit_sock" or k == "uevent_sock" or k == "cdev" or k == "init_net":
		continue
	if k == None:
		continue
	symcounter += 1
	p = Memory(*v) 
	print "comparing: ", k
	total, faults = p.memcmp()
	symcounter += total
	errorcounter += faults

  print "stats:"
  print "total symbols: %i, stayed same: %i, differring: %i, errors: %i" % (symcounter, samecounter, diffcounter, errorcounter)
  print "%f %% symbols changed or had errors" % (100.0 - (((samecounter + diffcounter) / (1.0 * symcounter)) * 100.0))
