#!/usr/bin/python
# -*- coding: utf-8 -*-
# analises trouble areas and prints dump statistics

from tools import *

def base_check(typ, backtrace=None):
    if backtrace is None: backtrace = []
    base = typ.base
    if base is None: return None
    backtrace.append((base, typ.name))
    if not base in typ.type_list: return backtrace
    return base_check(typ.type_list[base], backtrace)
    
if __name__ == "__main__":
    names, types, addresses = init(parents=True)

    arrays    = filter(lambda t: isinstance(t, Array), types.values())
    errors    = {'bound': 0, 'key': 0, 'size': 0, 'base': 0, 'hashtables': 0, 'hash_nodes': 0}
    dict_join = lambda x: "\n".join(["%15s := %d" % (k, v) for k,v in x.iteritems()])

    for t in types.values():
	ret = base_check(t)
	if ret is not None:
	    #errors['base'] += 1
	    print "base error", ret

    for a in arrays:
	if a.bound is None:
	    errors['bound'] += 1
	    print "missing bound information", a.get_name(), get_parent_names(a)
	try:
	    if a.get_element_size() is None:
		print "missing size information", a, hex(a.id)
		errors['size'] += 1
	except KeyError:
	    print "KeyError for %x" % (a.id)
	    errors['key'] += 1

    structs = filter(lambda t: isinstance(t, Struct), types.values())
    h_nodes = {}
    h_tables = {}

    
    for s in structs:
	for m in s:
	    if m.base and m.get_base().name == "hlist_node":
		print " hash_node in %s\t%d" % (s.get_name(), s.size)
		h_nodes[m.id] = 1
		errors['hash_nodes'] += 1
		
    for s in types.values():
	for m in s.bases():
	    if m.name == "hlist_head":
		print "Hashtable in %s\t(%s) → %s" % (s.get_name(), get_parent_names(s), m.name)
		errors['hashtables'] += 1
		h_tables[s.id] = 1
    for s in types.values():
	for m in s.bases():
	    if m.id in h_nodes: break
	    if m.name == "hlist_node":
#		if not s.id in h_nodes:
		  h_nodes[s.id] = 1
#		  for i in s.bases():
#		    h_nodes[i.id] = 1
		  errors['hash_nodes'] += 1
		  print " (x) hash_node in %s\t(%s)\t(%s)" % (s.get_name(), get_parent_names(s), ", ".join([i.get_name() for i in s.bases()]))
		  break

    print "Zusammenfassung\n", dict_join(errors)
