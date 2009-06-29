#!/usr/bin/python
import re, sys
from cPickle import dump, load

def dump_sysmap(dumpfile, sysmap):
    mapfile = open(sysmap, 'r')
    sympat = re.compile('([a-f0-9]+) (.) (\w+)')
    forward = {}
    backward = {}
    for line in mapfile:
        ret = sympat.search(line.strip())
        if not ret:
             continue
        addr, t, name = ret.groups()
	intaddr = int(addr, 16)
        forward[name] = intaddr 
        backward[intaddr] = name
    dump((forward, backward), open(dumpfile, 'w'))

def print_symbols(dumpfile):
	forward, backward = load(open(dumpfile, 'r'))
	for k,v in forward.iteritems():
		print k, "\t", v

if __name__ == '__main__':
	from os import popen
	SYSMAP_DUMP = "sysmap.dump"

	if len(sys.argv) < 2:
		print ("%s (readmap|print)" % sys.argv[0])
		sys.exit(1)
	if sys.argv[1] == "readmap":
		dump_sysmap(SYSMAP_DUMP, sys.argv[2])
	elif sys.argv[1] == "print":
		print_symbols(sys.argv[2])
