#!/usr/bin/python
# -*- coding: utf-8 -*-

import zmq
import argparse
import feedparser
import datetime
import time
import json
import util

def getTimestamp(t):
	"""converts time-tuple from feedparser into datetime object"""
	return datetime.datetime(t.tm_year, t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min, t.tm_sec)

def sorting_key(elem):
	"""docstring for entry_sorting"""
	elem_date = datetime.datetime.min
	for key in ['created_parsed', 'published_parsed', 'updated_parsed']:
		if elem.has_key(key):
			elem_date = max(elem_date, getTimestamp(elem[key]))
	return elem_date

def main(host, port, feedurl, topic):
	# connect
	context = zmq.Context.instance()
	publisher = context.socket(zmq.PUB)
	publisher.connect("tcp://{0}:{1}".format(host, port))

	# save previous timestamp that updates are recognized
	previous_update = datetime.datetime.min
	print 'press [CTRL] + [C] to quit'
	while True:
		try:
			data = feedparser.parse(feedurl)
			for entry in sorted(data['entries'], key=sorting_key):
				updated = sorting_key(entry)
				if updated > previous_update:
					previous_update = updated
					datum = {}
					for key, value in entry.iteritems():
						if isinstance(value, list) or isinstance(value, dict):
							pass
						elif key in ['published', 'updated', 'created', 'expired']:
							pass
						elif isinstance(value, time.struct_time):
							datum[key] = getTimestamp(value)
						else:
							datum[key] = value
					#push data
					publisher.send_multipart([topic, json.dumps(datum, cls=util.JSONEncoder)])

			# sleep until next update
			now = datetime.datetime.now()
			next_update = now.replace(second=0, microsecond=0) + datetime.timedelta(minutes=5 - now.minute % 5)
			time.sleep((next_update - now).total_seconds())
		except KeyboardInterrupt:
			break
		except Exception, e:
			print "error:", e

	# clean up
	publisher.close()
	context.term()

if __name__ == '__main__':
	argparser = argparse.ArgumentParser(
		description='publishes feed data from webfeed or local feed',
	)
	argparser.add_argument('-H', '--host', type=str, default='localhost', help='host to connect to')
	argparser.add_argument('-p', '--port', type=int, default='5559', help='port to connect to')
	argparser.add_argument('-t', '--topic', type=str, default='/feed', help='topic to publish to')
	argparser.add_argument('url', type=str, help='URL of the feed')

	try:
		args = argparser.parse_args()
	except IOError, msg:
		argparser.error(str(msg))

	main(args.host, args.port, args.url, args.topic)

