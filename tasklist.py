# -*- coding: utf-8 -*-
from tools import *

#------------------------------------------------------------------------------
def cstring(pchar, maxlen = -1):
	"""
	Returns the command a task_struct was running
	"""
	s = ""
	i = 0
	while (maxlen >= 0 and maxlen < i) or (maxlen < 0 and pchar[i].get_value() != 0):
		#print "--", i, pchar[i].get_value(), "%c" % pchar[i].get_value()
		s += "%c" % pchar[i]
		i += 1
	return s

#------------------------------------------------------------------------------
def task_cmd(task):
	"""
	Returns the command a task_struct was running
	"""
	return cstring(task.comm)

#------------------------------------------------------------------------------
def task_pwd(task):
	"""
	Returns the command a task_struct was running
	"""
	dname = task.fs.pwd.dentry.d_name.resolve()
	return cstring(dname.name, dname.len.get_value())

#------------------------------------------------------------------------------
def ps():
	"""
	Prints out a list of the tasks
	"""
	#global kernel_name
	it = kernel_name('init_task')
	task = it.tasks.next

	print "%5s  %5s  %5s  %5s  %-18s  %-16s  %s" % (
		"UID", 
		"PID",
		"TGID",
		"PPID",
		"ADDRESS",
		"PWD",
		"COMMAND"
	) 

	while (task.get_loc() != it.get_loc()):
		print "%5d  %5d  %5d  %5d  0x%0.16x  %-16s  %s" % (
			task.user.uid.get_value(), 
			task.pid.get_value(), 
			task.tgid.get_value(), 
			task.parent.pid.get_value(), 
			task.get_loc(),
			task_pwd(task),
			task_cmd(task)
		)
		task = task.tasks.next


#------------------------------------------------------------------------------
def pstree():
	"""
	Prints out the tree of the tasks
	"""
	it = kernel_name('init_task')
	print_task_tree(it.tasks.next)

#------------------------------------------------------------------------------
def print_task_tree(task, indent = 0):
	"""
	Prints out a task recursively
	"""
	
	if (indent > 10): return
	
	# Print out current task
	print "%s|-- %s (0x%0.16x)" % ("|   "*indent, str(task.pid), task.get_loc())
	#print " "*indent, task.pid.resolve(), task.get_loc()

	# Print out children
	try:
		# strange behaviour here:
		#  if there are children and we want to get them
		#   we have to access with offset -16 since it actually
		#   points to the sibling inside the children
		#  if there are no children it points to the children
		#   of itself, without any offset, just like expected
		#   normally
		if task.children.next.get_loc() == task.get_loc():
			return
		head = child = task.children.next_with_offset(-16)
		first = True
		while (first) or (child.get_loc() != head.get_loc()):
			print "|   "*(indent+2)
			print_task_tree(child, indent + 1)
			child = child.sibling.next
			# again strange bahaviour:
			# if there is a next sibling, which is not the first one
			#  then everything works like expected
			# if the current processed was the last child, then the
			#  sibling.next doesn't point back to the first, instead the
			#  sibling.next.sibling.next points at the first. In this case
			#  the sibling.next seems nothing useful
			if child.sibling.next.get_loc() == head.get_loc():
				break
			first = False
	except NullPointerException:
		# Just ignore null-pointer exceptions
		print "|   "*indent + '`- Caught NullPointerException'
		return
		#pass
