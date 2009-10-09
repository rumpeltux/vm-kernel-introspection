# -*- coding: utf-8 -*-
import re
from tools import *
from tools.xml_report import XMLReport

def ll_name(a, b):
  b = re.sub(r'\[.+?\]', '[]', b) #replace any indexes in array notation
  if a is not None:
      return a+'.'+b
  return b

def load_references(filename="meta_info.dump"):
  refs = load(open(filename))
  out = {}
  #(line, a,b, c,d)
  for i in refs:
    if i[2] is None:
      i = (i[0], i[2], i[1], i[3], i[4])
    name = ll_name(i[1], i[2])
    out[name] = out.get(name, []) + [i]
  return out

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
      if bases == []: raise KeyError(first_name)
    
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
    return (first_struct, last_member, offset)

def clone_and_replace(chain, new_tail):
  #requires extensions: clone, parents
  # not good at all yet…
  new_tail.register()
  old = chain[-2]
  chain[-2].base = new_tail.id
  chain[-1] = new_tail

def prepare_list_heads(do_report=False):
  """
  kernel lists are a special thing and need special treatment
  this routine replaces all members of type struct list_head with
  an appropriate replacement that takes care handling these lists
  """
  #TODO: in progress of rewriting, not working yet
  member_list = []
  array_handlers = []
  
  errors = {}
  questionable = 0
  
  if do_report:
    rep = XMLReport('list-heads')
  
  def log(node_name, e, name, line, s, t, a, b, c, d):
    if do_report:
      node = rep.add(node_name)
      errors[node_name] = errors.get(node_name, 0) + 1
      node.setAttribute('name', name)
      node.setAttribute('line', line)
      node.setAttribute('info', repr((a,b,c,d)))
      node.setAttribute('source-chain', str(s).replace('>', '}').replace('<', '{'))
      node.setAttribute('target-chain', str(t).replace('>', '}').replace('<', '{'))
      if e is not None: node.setAttribute('exception', repr(e) if isinstance(e, Exception) else str(e))
  
  def length_limited_types_of(x): # just for xml output
      res = types_of(x)
      return str(res if len(res) < 5 else res[:5] + ["..."]).replace('>', '}').replace('<', '{')
      
  refs = load_references()
  for name, named_refs in refs.iteritems():
   for (line, a,b, c,d) in named_refs:
    try:
      source_chains = name_resolver(name)
      #print name, ":", a
    except Exception, e:
      log('source-name-error', e, name, line, " ;; ".join([length_limited_types_of(i) for i in [a,b]]), "", a, b, c, d)
      continue
    try:
      target_chains = name_resolver("%s.%s" % (c, d))
      #print "  → %s.%s: %s" % (c, d, str(b))
    except Exception, e:
      log('target-name-error', e, name, line, source_chains, " ;; ".join([length_limited_types_of(i) for i in [c,d]]), a, b, c, d)
      continue
    
    #filter for list_head structs (or already converted linked lists)
    target_chains = [chain for chain in target_chains if chain[-1].name == 'list_head' or isinstance(chain[-1], KernelDoubleLinkedList)]
    
    #calculate the (struct, final_member, offset)s for each chain
    res = [get_chain_offset(chain) for chain in target_chains]
    
    #sanity checks
    if len(res) == 0: #no chain found
      log('no-chain', " ;; ".join([length_limited_types_of(i) for i in [a,b,c,d]]), name, line, source_chains, target_chains, a, b, c, d)
    else: #check if offset is the same for each chain
      last = res[0]
      error = False
      for i in res[1:]:
	if last[2] != i[2] and i[2] != 0:
	  error = True #bad because we would not know which one is right
	  log('multiple-offsets', res, name, line, source_chains, target_chains, a, b, c, d)
	  break
      
      if not error:
	#now save each chain
	for i in range(0, len(source_chains)):
	  #filter a couple of cases that do not end in a list_head
	  chain = source_chains[i]
	  if chain[-1].name != 'list_head' or (not isinstance(chain[-2], Member) and not isinstance(chain[-2], Variable)):
	    continue #TODO how about pointer, arrays?
	    
	  if len(chain[-2].parents) > 1:
	    log('multiple-parents', (i, chain[-2].parents), name, line, source_chains, target_chains, a, b, c, d)
	    
	  tail = chain[-1]
	  if isinstance(tail, KernelDoubleLinkedList):
	    print "already registered", repr(tail)
	    if tail.offset != res[0][2]:
	      log('different-offset', (tail, res), name, line, chain, target_chains, a, b, c, d)
	    continue
	  #TODO: here we still assume all target-chains are equal. are they?
	  new_tail = KernelDoubleLinkedList(res[0][0], chain[-2], res[0][2]) #struct, member, offset
	  log('SUCCESS', None, name, line, chain, target_chains, a, b, c, d)
	  clone_and_replace(chain, new_tail)
	#TODO Arrays: [[<c_types.Variable instance 'ptype_base'>, <c_types.Array instance 'list_head'>, <c_types.Struct instance 'list_head'>, <c_types.Struct instance 'list_head'>]]
	#errors = [i for i in a if i[-1].name != 'list_head']
	#sources = [i for i in a if i[-1].name == 'list_head']
	#if len(set(sources)) >= 0: print "=====", name, a
	#print len(a), a
	
  if do_report:
    node = rep.add('summary')
    for k,v in errors.iteritems():
      node.setAttribute('%s-errors' % k, str(v))
    
    print rep
    
if __name__ == '__main__':
    #generate the report
    init(parents=True)
    prepare_list_heads(do_report=True)
    sys.stderr.write("sanity check\nmodules → %s\n" % str(type_of('modules')))
    sys.stderr.write("init_task.children → %s\n" % str(type_of('init_task').resolve()[0]['children']))