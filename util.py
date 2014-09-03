#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import datetime

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
		else:
			return super(JSONEncoder, self).default(obj)
