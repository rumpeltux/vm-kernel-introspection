# -*- coding: utf-8 -*-
from tools import *
from cPickle import dump, load
import sys

def cleanup(revmap):
	print "cleanup ... ",
	l = []
	for i in revmap:
		l.append(i)
	del revmap
	l.sort(lambda x, y: x[0] < y[0])
	for i in range(1, len(l)):
		if cmp(l[i -1][0], l[i][0]) == 0:
			l[i - 1] = l[i]
	print "ready"
	rset = set(l)
	del l
	return rset

if __name__=='__main__':
  if len(sys.argv) < 3:
	  print "usage: ", sys.argv[0], "<memory image> <reverse map dumpfile>"
	  sys.exit(1)
 	
  dumpfile = sys.argv[2]
  fdump = open(dumpfile, "w")
  img = sys.argv[1]

  types, names, addresses = init(img)

  pgt = kernel_name('__ksymtab_init_level4_pgt')
  memory.set_init_level4_pgt(int(pgt.value.get_value()))

# recursionlimit at 1000 per default, but thats not enough
  sys.setrecursionlimit(8000)

#  temp = kernel_name('fib6_rules_ops_template')
#  revmap, faults = temp.revmap()
#  sys.exit(0)

  symcounter = 0
  errorcounter = 0
  grevmap = []

  print "calculating reverse maps:"
  totallen = len(addresses)
  pos = 0
  for k,v in addresses.iteritems():
	if k == None:
		continue
	symcounter += 1
	p = Memory(*v) 
	if pos % 10 == 0:
		print pos, "/", totallen, ": ", k, " "*(40), "\r",
	revmap, faults = p.revmap()
	grevmap[-1:] = revmap
	#grevmap.append(revmap)
#	grevmap = cleanup(grevmap)
	symcounter += len(revmap)
	errorcounter += faults
	pos += 1

  print "stats:"
  print "total symbols: %i, errors: %i" % (symcounter, errorcounter)

  print "saving revmap to ", dumpfile
  dump(grevmap, fdump) 
  print "done"
