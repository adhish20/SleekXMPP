import os
import logging

class Logger:
	"""An API for storing and retrieving History Information"""

	def LocalStore(self, jid, timestamp, node, typename, field, value, unit):
		"""Stores Timestamped Values of Fields of a Jid in Files as a Log for History"""

		if not os.path.exists(jid.node):
			os.makedirs(jid.node)
		os.chdir(jid.node)

		info = timestamp+'; '+node+'; '+typename+'; '+field+'; '+value+'; '+unit+'\n'

		with open(field+'.log', 'a') as f:
			f.write(info)

		os.chdir('..')
		return

	def LocalRetrieve(self, jid, field, fromTime, toTime):
		"""Retrieves History from Local Storage"""

		os.chdir(jid.node)
		timestamp = []
		node = []
		typename = []
		name = []
		value = []
		unit = []
		with open(field+'.log', 'r') as f:
			for line in f:
				line.split('; ')
				if line[0] > fromTime and line[0] < toTime:
					timestamp.append(line[0])
					node.append(line[1])
					typename.append(line[2])
					name.append(line[3])
					value.append(line[4])
					unit.append(line[5].split('\n')[0])
		return timestamp, node, typename, name, value, unit
