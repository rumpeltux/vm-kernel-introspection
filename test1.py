# -*- coding: utf-8 -*-
from tools import *
from tasklist import *

names, types, addresses = init('../ubuntu_memdump_before_terminal.dump')

it = kernel_name('init_task')

pstree()
