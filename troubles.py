#!/usr/bin/python
# -*- coding: utf-8 -*-
# analises trouble areas and prints dump statistics
from xml.dom.minidom import Document

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
    doc = Document()
    
    #some xml helpers
    def add(node, name):
	elem = doc.createElement(name)
	node.appendChild(elem)
	return elem
      
    text = lambda node, text: node.appendChild(doc.createTextNode(text))
    
    def set_node_info(node, typ):
	node.setAttribute("type-id", hex(typ.id))
	node.setAttribute("name", typ.get_name())

    def save_parents(s, node, v=None, d=0):
	"""
	appends references to Type s as xml <parents> to node
	"""
	if v is None: v = set([s.id])
	if len(s.parents) == 0 or d>1: return
	p = add(node, "parent")
	set_node_info(p, s)
	
	for i in s.parents:
	  if not i.id in v:
	    v.add(i.id)
	    save_parents(i, p, v, d+1)
    
    #other helpers
    dict_join = lambda x: "\n".join(["%15s := %d" % (k, v) for k,v in x.iteritems()])

    #summary
    errors    = {'bound': 0, 'key': 0, 'size': 0, 'base': 0, 'hashtables': 0, 'hash_nodes': 0}

    report = add(doc, "report")
    
    #go arrays!
    doc_arrays = add(report, "arrays")
    arrays    = filter(lambda t: isinstance(t, Array), types.values())

    for a in arrays:
	if a.bound is None:
	    errors['bound'] += 1
	    bound = add(doc_arrays, "bound")
	    set_node_info(bound, a)
	    save_parents(a, bound)
	if a.get_element_size() is None:
	    size = add(doc_arrays, "size")
	    set_node_info(size, a)
	    text(size, a)
	    errors['size'] += 1

    #go hashtables!
    doc_hash = add(report, "hashtables")
    structs = filter(lambda t: isinstance(t, Struct), types.values())
    h_nodes = {}
    h_tables = {}
    
    #scan all structs for members of type hlist_node
    # these are actual hashtable entries
    for s in structs:
	for m in s:
	    if m.base and m.get_base().name == "hlist_node":
		node = add(doc_hash, "hlist_node")
		set_node_info(node, s)
		node.setAttribute("size", str(s.size))
		node.setAttribute("pointers", str(check_node_for_pointers(s)))
		
		member = add(node, "member")
		set_node_info(member, m)
		
		h_nodes[m.id] = 1
		errors['hash_nodes'] += 1

    #scan all types references to hlist_head
    # these are entry points to hashtables
    for s in types.values():
	if s.name == "hlist_head":
	    node = add(doc_hash, "hlist_head")
	    set_node_info(node, s)
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

    doc_sum = add(report, "summary")
    for (k,v) in errors.iteritems():
      add(doc_sum, k).setAttribute("count", str(v))
    
    return doc
    
if __name__ == "__main__":
    names, types, addresses = init(parents=True)
    
    print generate_report().toprettyxml(indent="  ")
