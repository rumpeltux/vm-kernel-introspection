# -*- coding: utf-8 -*-
# implementation of tool-functions for convenient use

from c_types import *
from c_types.user_types import *

from memory_manager import *
import os
from cPickle import load

#type_of_address = lambda y: types[memory[y]]

#creates a new memory instance of type type at the same location as memory
cast = lambda memory, type: Memory(memory.get_loc(), type)
#returns the first suiting type named name
type_of = lambda name: types[names[name][0]]
#returns all types named name
types_of = lambda name: [types[i] for i in names[name]]
#creates a pointer to the first suiting type named name
pointer_to = lambda name: Pointer(type_of(name), types)
#returns a memory instance of a global kernel variable named name
kernel_name = lambda name: Memory(*addresses[name])

def get_parent_names(s, v=None, d=0):
    """
    returns a string representation of references to Type s
    e.g. "{foo, bar} ← s.name"
    """
    if v is None: v = set([s.id])
    if len(s.parents) == 0 or d>1: return s.get_name()
    l = []
    for i in s.parents:
      if not i.id in v:
	v.add(i.id)
	l.append(get_parent_names(i, v, d+1))
    return "{%s} ← %s" % (", ".join(l), s.get_name())

def prepare_void_references(types):
    """
    void references (type.base is None) are not accounted for during the parsing process
    this function replaces those None references for Pointers and Consts by the Void-Type which has id 0
    """
    void = Void(types)
    for id, typ in types.iteritems():
      if isinstance(typ, Pointer) or isinstance(typ, Const):
	if typ.base is None:
	  typ.base = void.id #(void.id == 0)

def handle_array(array, member, struct, cls):
  """
  Replacing struct list_heads is difficult for Arrays
  So here we implement the special handling for this case.
  
  We create a pseudo member element for each array idx
  and then transform it into a KernelLinkedList that gets
  appended to the original data structure.
  Finally the obsolete array is removed from there
  """
  
  idx = 0
  for entry,offset in array.__iter__(loc=0):
    pseudo_member = Type()
    pseudo_member.name = "%s_%d" % (member.name, idx)
    pseudo_member.offset = member.offset + offset
    new_element = cls(struct, pseudo_member)
    new_element.register()
    struct.append(new_element)
    idx += 1
  struct.members.remove(member.id)
  #cannot delete it because it might be referenced by other structs!
  #del types[member.id]

def load_references(filename="meta_info.dump"):
  refs = load(open(filename))
  out = {}
  #(line, a,b, c,d)
  for i in refs:
    if i[2] is None:
      i = (i[0], i[2], i[1], i[3], i[4])
    b = re.sub(r'\[.+?\]', '[]', i[2]) #replace any indexes in array notation
    if i[1] is not None:
      out[i[1]+'.'+b] = i
    else:
      out[b] = i
  return out

from linked_lists import *

def prepare_list_heads_todo():
  
  for k,v in types.iteritems():
    if isinstance(v, Struct):
      for member in v:
	lh = member.get_base()
	if lh and lh.name:
	  if lh.name == "list_head":
	    print "checking '%s'.'%s'" % (v.get_name(), member.get_name()),
	    name = '%s.%s' % (v.get_name(), member.get_name())
	    if name in refs:
	      print "found at %s → '%s'.'%s'" % (refs[name][0], refs[name][3], refs[name][4])
	      #print get_type(refs[name][3], refs[name][4])
	    else:
	      print "not found"
	    #member_list.append((KernelDoubleLinkedList(v, member), member))
	if isinstance(lh, Array) and lh.get_base():
	  ar_lh = lh.get_base()
	  if ar_lh.name == "list_head":
	    print "not yet handling array at '%s'.'%s'" % (v.get_name(), member.get_name())
	    #array_handlers.append((lh, member, v, KernelDoubleLinkedList))

  for val in array_handlers:
    handle_array(*val)
	  
  for new_member, old_member in member_list:
      new_member.takeover(old_member)

def prepare_strings():
    """
    Assume that all pointers to a char-type are strings.
    Modify that data model accordingly
    """
    typ_list = []

    for k,v in types.iteritems():
	if isinstance(v, Pointer):
	    b = v.get_base()
	    if isinstance(b, BasicType) and (b.name == "char" or b.name == "unsigned char"):
		typ_list.append((String(v), v))

    for s,v in typ_list:
      s.takeover(v)

def init(filename=None, parents=False, system_map=False):
    """
    helper function to initialise a dump-session.

    filename is the path to the memory dump e.g /dev/mem.
    if parents is set, parent relationships for data types will be available.
    if system_map if set to a filename, this file is interpreted as
      a System.map and all its symbols will become available in the program (TODO)
      additionally other sources to load symbols will be loaded from the memory image
    """
    import memory, type_parser
    global types, names, addresses
    if filename is not None:
	filesize = 4 * 1024**3 if filename == "/dev/mem" else os.path.getsize(filename)
	memory.map(filename, filesize, filesize, 0)
    types, memory = type_parser.load(open("data.dumpc"))

    if parents:
	from c_types.extensions import parents
	parents.enumerate_parents(types)

    names = {}
    for k,v in types.iteritems():
      names[v.name] = names.get(v.name, []) + [k]

    addresses = {}
    for k,v in memory.iteritems():
      addresses[types[v].name] = (k, types[v])

    #some more cleanup i forgot once. is already obsolete…
    #pat3= re.compile('DW_OP_plus_uconst: (\d+)')
    #for k,v in types.iteritems():
	#if hasattr(v, "offset") and type(v.offset) != int:
	    #v.offset = int(pat3.search(v.offset).group(1))
    
    if filename is not None and system_map:
      #TODO: load_system_map(system_map)
      load_additional_symbols()

    #TODO effizienter implementieren. 
    #ev. callbacks die an den einzelnen stellen registriert werden
    prepare_list_heads()
    prepare_strings()
    prepare_void_references(types)

    return names, types, addresses

def strings(phys_pos, filename):
  import memory
  f = open(filename, "w")
  while 1:
    s = memory.access(10, phys_pos)
    print >>f, "%08x\t%s" % (phys_pos, repr(s))
    phys_pos += len(s) + 1

def load_additional_symbols():
  pgt = kernel_name('__ksymtab_init_task') #first element
  syms = cast(pgt, Array(pgt.get_type()))
  i = 0
  try:
   while 1:
    name, value = str(cast(syms[i].name, Pointer(String(Array(type_of('unsigned char')))))), hex(syms[i].value)
    if not name in addresses and name in names: addresses[name] = (int(syms[i].value), type_of(name))
    i += 1
  except: pass

def dump_pagetables(pgt4, filename):
  f = open(filename, "w")
  page = lambda x: (x & ~0x8000000000000fff) + 0xffff880000000000
  is_null = lambda x: x.get_loc() == 0xffff880000000000
  loc  = lambda x: x.get_loc() - 0xffff880000000000
  for i in range(512):
    pud = Memory( page(pgt4[i].pgd.get_value()[1]), type_of('level3_kernel_pgt')) #raw addresses
    if not is_null(pud):
      print >>f, "  [%03d] --> %x" % (i, loc(pud))
      for j in range(512):
	pmd = Memory( page(pud[j].pud.get_value()[1]), type_of('level2_kernel_pgt'))
	if not is_null(pmd):
	  print >>f, "     [%03d] --> %x" % (j, loc(pmd))
	  for k in range(512):
	    pte = Memory( page(pmd[k].pmd.get_value()[1]), type_of('level2_kernel_pgt'))
	    if not is_null(pte) and pmd[k].pmd.get_value()[1] & 0x80 == 0: #skip LARGE PAGES for now
	      print >>f, "        [%03d] --> %x" % (k, loc(pte))
	      for l in range(512):
		if pte[l].pmd.get_value()[1] != 0:
		  print >>f, "           [%03d] --> %x" % (l, pte[l].pmd.get_value()[1])
  f.close()
