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
		head = child = task.children.next
		first = True
		while (first) or (child.get_loc() != head.get_loc()):
			print "|   "*(indent+2)
			print_task_tree(child, indent + 1)
			child = child.sibling.next
			first = False
	except NullPointerException:
		# Just ignore null-pointer exceptions
		print "|   "*indent + '`- Caught NullPointerException'
		return
		#pass

names, types, addresses = init('../ubuntu_memdump_before_terminal.dump')

ps()
