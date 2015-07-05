#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import datetime
import geopy
import gzip
import os
import logging.handlers

class JSONEncoder(json.JSONEncoder):
	"""extending JSONEncoder to serialize more types (e.g. datetimes)"""
	def __init__(self, **kwargs):
		super(JSONEncoder, self).__init__(**kwargs)

	def default(self, obj):
		if isinstance(obj, datetime.datetime):
			return obj.isoformat()
		elif isinstance(obj, datetime.date):
			return obj.isoformat()
		elif isinstance(obj, datetime.time):
			return obj.isoformat()
		elif isinstance(obj, geopy.Point):
			return str(obj)
		else:
			return super(JSONEncoder, self).default(obj)

class TimedCompressingRotatingFileHandler(logging.handlers.TimedRotatingFileHandler):
	"""added gzip compression for TimedRotatingFileHandler"""
	def __init__(self, filename, when='h', interval=1, backupCount=0, encoding=None, delay=False, utc=False, atTime=None):
		super(TimedCompressingRotatingFileHandler, self).__init__(filename=filename, when=when, interval=interval, backupCount=backupCount, encoding=encoding, delay=delay, utc=utc, atTime=atTime)

		self.namer = lambda name: name + '.gz'

		def compression_rotator(source, dest):
			data = open(source, 'rb').read()
			os.remove(source)
			df = gzip.open(dest, 'wb')
			df.write(data)
			df.close()
		self.rotator = compression_rotator

