# -*- coding: utf-8 -*-
from tools import *

names, types, addresses = init('../ubuntu_memdump_before_terminal.dump')

it = kernel_name('init_task')
p = it.tasks.next

child = p.children.next
par = child.parent
bla = par.resolve()

print "bla"
print bla.pid
