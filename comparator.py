# -*- coding: utf-8 -*-

class Comparator():
	"""
	Manages an internal list of symbols to compare and then compares then
	"""
# TODO: first do it non-threaded
#	then enhance!
	queue = set({})
	seen = {}

	def __init__(self):
		pass
		
	def enqueue(self, type, loc, loc1):
		"""
		Enqueue an item to the compare list
		"""
		try:
			if self.seen[type] != None:
				if loc in self.seen[type]:
					return
				else:
					self.seen[type].append(loc)
					self.queue.append((type, loc, loc1))
		except KeyError, e:
			self.seen[type] = set([loc])
			self.queue.append((type, loc, loc1))
		return


