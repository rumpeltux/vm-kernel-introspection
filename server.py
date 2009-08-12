#!/usr/bin/python
# -*- coding: utf-8 -*-
# This is a server listening on a TCP-Socket providing a python shell
# can then be used to quickly post questions or perform queries on the
# data model.

import code, sys, os
from tools import *
from twisted.protocols import basic

class MemoryServer(basic.LineReceiver):
  shell = None
  def lineReceived(self, line):
    if self.shell is None:
      self.shell = code.InteractiveConsole()
      self.shell.write = lambda data: self.sendLine(data)
    self.shell.push(line) # == 1: #line was processed

from twisted.internet.protocol import ServerFactory
factory = ServerFactory()
factory.protocol = MemoryServer

if __name__=='__main__':
  from twisted.application import service, internet
  application = service.Application("memoryserver")
  internet.TCPServer(1025, factory).setServiceParent(application)

  