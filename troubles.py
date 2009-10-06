#!/usr/bin/python
# -*- coding: utf-8 -*-
# analises trouble areas and prints dump statistics
from xml.dom.minidom import Document
from tools.xml import XMLReport
from tools import *

def base_check(typ, backtrace=None):
    if backtrace is None: backtrace = []
    base = typ.base
    if base is None: return None
    backtrace.append((base, typ.name))
    if not base in typ.type_list: return backtrace
    return base_check(typ.type_list[base], backtrace)

def check_node_for_pointers(node):
    """
    returns the number of elements in a struct and its members
    that are pointers to other values
    """
    #if v is None: v = set([node.id])
    
    counter = 0
    for member in node:
      for base in member.bases():
	#if base.id in v: continue
	if isinstance(base, Struct):
	  counter += check_node_for_pointers(base)
	if isinstance(base, Pointer):
	  counter += 1
	  break
    return counter

def generate_report():
    report = XMLReport('report')

    def save_parents(s, node, v=None, d=0):
	"""
	appends references to Type s as xml <parents> to node
	"""
	if v is None: v = set([s.id])
	if len(s.parents) == 0 or d>1: return
	p = report.add("parent", node)
	report.set_node_info(s, p)
	
	for i in s.parents:
	  if not i.id in v:
	    v.add(i.id)
	    save_parents(i, p, v, d+1)
    
    #other helpers
    dict_join = lambda x: "\n".join(["%15s := %d" % (k, v) for k,v in x.iteritems()])

    #summary
    errors    = {'bound': 0, 'key': 0, 'size': 0, 'base': 0, 'hashtables': 0, 'hash_nodes': 0}

    #go arrays!
    doc_arrays = report.add("arrays")
    arrays    = filter(lambda t: isinstance(t, Array), types.values())

    for a in arrays:
	if a.bound is None:
	    errors['bound'] += 1
	    bound = report.add("bound", doc_arrays)
	    report.set_node_info(a, bound)
	    save_parents(a, bound)
	if a.get_element_size() is None:
	    size = report.add("size", doc_arrays)
	    report.set_node_info(a, size)
	    text(size, a)
	    errors['size'] += 1

    #go hashtables!
    doc_hash = report.add("hashtables")
    structs = filter(lambda t: isinstance(t, Struct), types.values())
    h_nodes = {}
    h_tables = {}
    
    #scan all structs for members of type hlist_node
    # these are actual hashtable entries
    for s in structs:
	for m in s:
	    if m.base and m.get_base().name == "hlist_node":
		node = report.add("hlist_node", doc_hash)
		report.set_node_info(s, node)
		node.setAttribute("size", str(s.size))
		node.setAttribute("pointers", str(check_node_for_pointers(s)))
		
		member = report.add("member", node)
		report.set_node_info(m, member)
		
		h_nodes[m.id] = 1
		errors['hash_nodes'] += 1

    #scan all types references to hlist_head
    # these are entry points to hashtables
    for s in types.values():
	if s.name == "hlist_head":
	    node = report.add("hlist_head", doc_hash)
	    report.set_node_info(node, s)
	    save_parents(s, node)
	    
	for m in s.bases():
	    if m.name == "hlist_head":
		#print "Hashtable in %s\t(%s) → %s" % (s.get_name(), get_parent_names(s), m.name)
		errors['hashtables'] += 1
		h_tables[s.id] = 1

    #whatever this code was for???
    #for s in types.values():
	#for m in s.bases():
	    #if m.id in h_nodes: break
	    #if m.name == "hlist_node":
		  ## not s.id in h_nodes:
		  #h_nodes[s.id] = 1
##		  for i in s.bases():
##		    h_nodes[i.id] = 1
		  #errors['hash_nodes'] += 1
		  ##print " (x) hash_node in %s\t(%s)\t(%s)" % (s.get_name(), get_parent_names(s), ", ".join([i.get_name() for i in s.bases()]))
		  #break

    doc_sum = report.add("summary")
    for (k,v) in errors.iteritems():
      add(doc_sum, k).setAttribute("count", str(v))
    
    return report
    
if __name__ == "__main__":
    names, types, addresses = init(parents=True)
    
    print generate_report()
