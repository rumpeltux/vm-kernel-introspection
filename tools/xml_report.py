# -*- coding: utf-8 -*-
#some xml helpers
from xml.dom.minidom import Document

class XMLReport:
      def __init__(self, name):
	self.doc = Document()
	self.main_node = self.add(name, node=self.doc)
    
      def add(self, name, node=None):
	if node is None: node = self.main_node
	elem = self.doc.createElement(name)
	node.appendChild(elem)
	return elem
      
      def text(self, text, node):
	node.appendChild(self.doc.createTextNode(text))
    
      def set_node_info(self, node, typ):
	node.setAttribute("type-id", hex(typ.id))
	node.setAttribute("name", typ.get_name())

      def __str__(self):
	return self.doc.toprettyxml(indent="  ")