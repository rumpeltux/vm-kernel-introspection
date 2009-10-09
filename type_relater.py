# -*- coding: utf-8 -*-
# Searches Linux Kernel Source for usages of kernel linked lists
# and tries to auto-associate members to members in the pointed-to structure
# e.g. task_struct.children.next should point to another_task_struct.children
#      but instead points to another_task_struct.sibling.
#      We can infer this relation by observing code for entries like:
# kernel/exit.c:890  list_for_each_entry_safe(p, n, &father->children, sibling)
#      then calculating the types of the involved variables will lead
#      to the desired relation

import os, sys, re
import type_parser
from tools.xml_report import XMLReport

def pp(file, line):
    "print path"
    return "%s:%d" % (file[len(sys.argv[1]):], line)

class DebugSymbols:
    """
    debug symbol reader for object files
    can then retrieve symbol information based on line-numbers in the source-file
    """
    filename = None
    types = None
    def __init__(self, file):
	self.filename = file
	
	#read the actual debug symbols
	fd = os.popen("objdump -g \"%s\" 2>/dev/null" % file, "r")
	types, memory = type_parser.read_types(fd, save_line_information=True)
	self.types = types
	
	self.names = {}
	for k,v in self.types.iteritems():
	  a = self.names.get(v.name, [])
	  a.append(v)
	  self.names[v.name] = a
    
    def get_type_at_line(self, name, line):
	cur = None
	for typ in self.names[name]:
	    #file 0 is other variables (externs?) all on line 0, so we might consider them as well
	    #file 1 is the source-file, others are included headers
	    if typ.line <= line and typ.file <= 1:
	      if not cur or cur.line < typ.line:
		  cur = typ
	# if we did not find a matching name in the source-file,
	# take the first remaining candidate (usually from headers)
	if cur is None:
	  cur = self.names[name][0] if name in self.names else None
	return cur

accessed_members = {}
referenced_members = {}
def member_access(type, member):
    "denotes that instances of type can be referenced by pointers to type.member"
    if not type in accessed_members:
      accessed_members[type] = []
    if not member in accessed_members[type]:
      accessed_members[type].append(member)
def member_reference(name, member):
    "denotes that instances of type can be referenced by pointers to type.member"
    if not name in referenced_members:
      referenced_members[name] = []
    if not member in referenced_members[name]:
      referenced_members[name].append(member)

match_expressions = [
	re.compile(r'(?P<name>list_for_each.*?)\((?P<args>.+)\)'),
	re.compile(r'(?P<name>list_(first_)?entry)\((?P<args>.+)\)')
      ]
	  
class TypeRelater:
    """
    performs the actual source-file analysation and the matching with
    debug symbols providing a list of references for further use
    """
    def __init__(self, file, report):
        "handles a single source file"
	
	handlers = {
	  'list_entry': self.list_access_handler,
	  'list_for_each': self.loop_begin_handler,
	  'list_for_each_safe': self.loop_begin_handler_safe,
	  'list_for_each_entry': self.untyped_access_handler,
	  'list_for_each_entry_rcu': self.untyped_access_handler,
	  'list_for_each_entry_reverse': self.untyped_access_handler,
	  'list_for_each_entry_safe': self.list_for_each_entry_safe,
	  'list_for_each_entry_safe_reverse': self.list_for_each_entry_safe
	}
	self.loop_refs = {}
	self.references = []
	self.report = report
	self.file = file
	self.line = 0
	for line in open(file):
	    self.line += 1
	    self.line_content = line
	    for exp in match_expressions:
		m = exp.search(line)
		if m:
		    name, args = m.group('name').strip(), m.group('args').split(",")
		    if args[-1].rstrip()[-1] == ')':
		      args[-1] = args[-1].rstrip()[:-1]
		    if name in handlers:
		      try:
			handlers[name](args)
		      except Exception, e:
			self.log('exception', name, args, extra=str(e))
		    else:
			self.log('unhandled', name, args)
			
    def log(self, group, info, args, extra=""):
	"saves a log-message"
	node = self.report.add(group)
	node.setAttribute('line', str(self.line))
	node.setAttribute('file', self.file)
	node.setAttribute('line-content', self.line_content)
	if extra != "": node.setAttribute('extra', extra)
	node.setAttribute('info', info)
	self.report.text(str(args), node)
	
    def register_ref(self, type, from_struct, from_member, to_struct, to_member):
	"registers a reference"
	def check_name(x, i):
	  if x is not None and re.compile(r'[^\w \.\-\>]').search(x):
	    self.log('name-error', x, str(i))
	check_name(from_struct, 0)
	check_name(from_member, 1)
	check_name(to_struct, 2)
	check_name(to_member, 3)
	self.references.append((pp(self.file, self.line), from_struct, from_member, to_struct, to_member))
	#print "%s_REF: %s: %s.%s → %s.%s" % (type, pp(self.file, self.line), from_struct, from_member, to_struct, to_member)
	
    # ----- debug symbol access ------
  
    dbg_syms = None
    def load_symbols(self):
	"reads debug symbols from file file"
	if not self.dbg_syms:
	  self.dbg_syms = DebugSymbols(self.file[:-1]+"o")

    def get_symbol_type(self, name):
	"returns a c_type instance for name's type at the current line"
	self.load_symbols()
	try:
	  typ = self.dbg_syms.get_type_at_line(name, self.line)
	except KeyError:
	  self.log('dbgsym-fail', name)
	  typ = None
	
	if typ:
	  typ = typ.resolve()[0]
	
	return typ

    # ----- source code handlers for regular expression matches ------
    
    def typed_access_handler(self, args):
	ptr, type, member = args
	if type.lstrip().startswith('struct'):
	    member_access(type.lstrip()[6:].strip(), member.strip())
	else:
	    pass #print "(uncatched)", args

    head_type_reference_re = re.compile('&(.+)->(.+)')
    def untyped_access_handler(self, args):
        """list_for_each_entry(pos, head, member)
	
	args looks usually like: ['pool', ' &dev->dma_pools', ' pools']
	we find out what type pos ('pool') actually is
	pos’ attribute 'pools' is referenced then by dev's type attribute 'dma_pools'
	
	so we find out what type 'dev' is and mark its attribute 'dma_pools'
	as referencing type_of('pool')’s member pools, so we can use it later
	
	sometimes head is '&some_list' which is thus a global variable being
	an entry point to some list of pos’ type
	"""
	
	#if len(args) != 3: return
	pos, head, member = args
	
	typ_pos = self.get_symbol_type(pos.strip())
	  
	match = self.head_type_reference_re.search(head)
	if match:
	    variable_name = match.group(1).strip()
	    member_name   = match.group(2).strip()
	    typ_head = self.get_symbol_type(variable_name)
	    
	    if typ_head and typ_pos:
	      self.register_ref('TYPE', typ_head.get_name(), member_name, typ_pos.get_name(), member.strip())
	      return
	if not match and typ_pos and head.lstrip()[0] == '&':
	    self.register_ref('GLOB', None, head.lstrip()[1:].strip(), typ_pos.get_name(), member.strip())
	    return
	self.log('uncatched', "untyped_access_handler", args)

	
    def list_for_each_entry_safe(self, args):
	#if len(args) != 4: return
	pos, n, head, member = args
	return self.untyped_access_handler((pos, head, member))

    def loop_begin_handler(self, args):
	""" handles beginning of loops and saves information
	
	access might look like that:
        list_for_each_safe(_chunk, _next_chunk, &pool->chunks) {
	    chunk = list_entry(_chunk, struct gen_pool_chunk, next_chunk);
	
	so here we infer that pool.chunks might reference another type through
	list_entry access on '_chunk'. """
	
	#if len(args) != 2: return
	pos, head = args
	
	match = self.head_type_reference_re.search(head)
	if match:
	    variable_name = match.group(1).strip()
	    member_name   = match.group(2).strip()
	    typ_head = self.get_symbol_type(variable_name)
	    
	    if typ_head:
	      self.loop_refs[pos.strip()] = (self.line, typ_head.get_name(), member_name)
	      return
	    
	    if head.lstrip()[0] == '&':
	      self.loop_refs[pos.strip()] = (self.line, None, head.lstrip()[1:].strip())
	      return
	    
	self.log('uncatched', "loop_begin_handler", args)

    def loop_begin_handler_safe(self, args):
	#if len(args) != 3: return
	pos, n, head = args
	self.loop_begin_handler((pos, head))
	
    def list_access_handler(self, args):
	""" see loop_begin_handler """
	#if len(args) != 3: return
	ptr, type, member = args
	ptr = ptr.strip()
	if ptr in self.loop_refs:
	  r = self.loop_refs[ptr]
	  self.register_ref('LIST-%d' % r[0], r[1], r[2], type.replace("struct ","",1), member)
	  return
	self.log('unreferenced', "list_access_handler", args)

def indicate_progress(a,b):
    sys.stderr.write('\rparsing progress: %.2f%%' % (100. * a / b))

def run(path, out_file):
    "handles all source-files"
    file_match = re.compile('.(c)$')
    
    refs = []
    
    sys.stderr.write('\rinitialisation…')
    report = XMLReport('report')
    
    #quickly count all files:
    count = 0
    for dirpath, dirnames, filenames in os.walk(path):
	for file in filenames:
	    if file_match.search(file): count += 1
	    
    #handle the actual processing
    i = 0
    for dirpath, dirnames, filenames in os.walk(path):
	for file in filenames:
	    if file_match.search(file):
	      i += 1
	      indicate_progress(i, count)
	      refs += TypeRelater(os.path.join(dirpath, file), report).references
    
    from cPickle import dump
    dump(refs, open(out_file, 'w'))
    print report

if __name__ == '__main__':
  from c_types.extensions import clean, compare, string, init
  if 0:
    
    s = DebugSymbols("/media/disk-1/build/linux-2.6.28/fs/dlm/config.o")
  else:
    run(sys.argv[1], sys.argv[2])
    for k, v in accessed_members.iteritems():
      if len(v) > 1:
	print "%s\t%s" % ( k, v )
	
    for k, v in referenced_members.iteritems():
	print "%s\t%s" % ( k, v )
