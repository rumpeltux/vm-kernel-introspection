# -*- coding: utf-8 -*-
import re
from tools import *

def name_resolver(name, bases=None):
    """
    resolves a type-reference by name and returns the chain of types leading there
    e.g: name_resolver('zone.free_area[].free_list[]')
    
    2 cases to handle
    a) name.value, name->value
    b) name[]
    """
    #base = type_of(a).resolve()
    elems = re.split(r'->|\.|\[\]', name)
    
    if bases is None:
      first_name = elems.pop(0)
      bases = types_of(first_name)
    
    out = []
    for i in bases:
      chain = _name_resolver(i, elems)
      if chain is not None:
	out.append(chain)
      
    return out

def _name_resolver(base, elements):
    """
    resolves a list of names from one starting type 'base'
    """
    chain = [base]
    base = base.resolve()[0]
    chain.append(base)
    
    for i in elements:
      name = i.strip()
      
      if name == '': #[] element (array)
	if not isinstance(base, Array):
	  return None
	base = base.get_base()
	
      else: #member access
	if not isinstance(base, Struct):
	  return None
	base = base[i]	#get the member named i
	
      if base is None: return None
      chain.append(base)
      base = base.resolve()[0]
      chain.append(base)
      
    return chain
    
def get_chain_offset(chain):
    """
    calculates the offset of the last member in the chain
    from the first struct of the chain
    """
    first_struct = None
    last_member  = None
    offset = 0
    for i in chain:
      if first_struct is None and isinstance(i, Struct):
	first_struct = i
      if isinstance(i, Member) and first_struct is not None:
	if last_member != i:
	  offset += i.offset
	last_member = i
      if isinstance(i, Pointer) or isinstance(i, Array): #sanity check
	raise Exception("list-fail %s" % repr(chain)) #we cannot follow links inside arrays or to pointers
    return offset

def prepare_list_heads():
  """
  kernel lists are a special thing and need special treatment
  this routine replaces all members of type struct list_head with
  an appropriate replacement that takes care handling these lists
  """
  #TODO: in progress of rewriting, not working yet
  member_list = []
  array_handlers = []
  
  name_a = 0
  name_b = 0
  no_chain = 0
  questionable = 0
  
  refs = load_references()
  for name, (line, a,b, c,d) in refs.iteritems():
    try:
      a = name_resolver(name)
      #print name, ":", a
    except Exception, e:
      #print "fail (%s): %s" % (str(e), name)
      name_a += 1
      continue
    try:
      b = name_resolver("%s.%s" % (c, d))
      #print "  → %s.%s: %s" % (c, d, str(b))
    except Exception, e:
      #print "fail (%s): %s.%s" % (str(e), c, d)
      name_b += 1
      continue
    
    #filter for list_head structs
    b = [chain for chain in b if chain[-1].name == 'list_head']
    res = [get_chain_offset(chain) for chain in b]
    if len(res) == 0:
      no_chain += 1
    else:
      last = res[0]
      for i in res[1:]:
	if last != i:
	  print "fragwürdig", (name, "%s.%s" % (c, d)), b, res
	  questionable += 1
	  break
  
  print "summary", name_a, name_b, questionable