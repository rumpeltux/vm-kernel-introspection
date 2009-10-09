#!/usr/bin/python -i
# -*- coding: utf-8 -*-
from tools import *
from cPickle import dump, load
import sys

if __name__=='__main__':
  if len(sys.argv) < 4:
	  print "usage: ", sys.argv[0], "<memory dump file> <reverse map dumpfile> <memory location>"
	  sys.exit(1)
 	
  memdumpfile = sys.argv[1]
  dumpfile = sys.argv[2]
  fdump = open(dumpfile, "r")
  sloc = sys.argv[3]

  if sloc[:2] == "0x":
	  loc = int(sloc, 16)
  else:
	  loc = int(sloc, 10)

  print "::: loading reverse mapping from file ", dumpfile
  revmap = load(fdump)
  print "::: searching for symbol in location ", hex(loc), "(", str(loc), ") ..."

  i = 0
  total = len(revmap)
  found = []
  for location, size, type in revmap:
  	if loc >= location and loc <= (location + size):
		print "found: @", hex(location), ", ", str(size), ", ", repr(type)
		found.append((location, size, type))
	if i % 300 == 0:
		print str(i), "/", total, "\r",
	i+=1

  print "::: deleting unused reverse mappings ..."
  del revmap

  print "::: loading symbols using memory dump from " + memdumpfile + "..."
  names, types, addresses = init(memdumpfile)
  print "::: you will find the found types in the local variable found ..."
