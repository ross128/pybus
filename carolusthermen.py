#!/usr/bin/python
# -*- coding: utf-8 -*-

import zmq
import argparse
import urllib2
import bs4
import datetime
import time

def retrieve_occupancy():
	'''retrieves data from the carolus thermen homepage'''
	request = urllib2.Request(
		'http://www.carolus-thermen.de/go/auslastung/english.html',
		headers={'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:28.0) Gecko/20100101 Firefox/28.0'}
	)
	data = urllib2.urlopen(request).read()
	tree = bs4.BeautifulSoup(data)

	occupancy = {}
	# update timestamp
	datestring = ' '.join( (e.getText() for e in tree('p', id='last_update')[0]('strong') ) )
	for suffix in ['th','st','nd','rd']:
		try:
			occupancy['update'] = datetime.datetime.strptime(datestring, '%B  %d' + suffix + '          \n, %Y  %I:%M %p')
			break
		except:
			pass

	# occupancy data
	categories = ['thermen', 'sauna', 'garage']
	for i,div in enumerate(tree.div(id='box_auslastungen')[0].find_all('div', 'inner')):
		occupancy[categories[i]] = int(div['style'][6:-2])

	return occupancy

def main(host, port):
	# connect
	context = zmq.Context.instance()
	publisher = context.socket(zmq.PUB)
	publisher.connect("tcp://{0}:{1}".format(host, port))

	# save previous timestamp that updates are recognized
	previous_update = datetime.datetime.min
	print 'press [CTRL] + [C] to quit'
	while True:
		try:
			occupancy = retrieve_occupancy()
			if occupancy['update'] > previous_update:
				previous_update = occupancy['update']
				for topic in ['update', 'thermen', 'sauna', 'garage']:
					publisher.send_multipart(['/carolus/{0}'.format(topic), str(occupancy[topic])])

			# sleep until next update (minute = 1, 6, 11, 16, ..., 56)
			now = datetime.datetime.now()
			next_update = now.replace(second=0, microsecond=0) + datetime.timedelta(minutes=6 - now.minute % 5)
			time.sleep( (next_update - now).total_seconds())
		except KeyboardInterrupt:
			break

	# clean up
	publisher.close()
	context.term()

if __name__ == '__main__':
	argparser = argparse.ArgumentParser(
		description='publishes occupancy data for the Carolus Thermen Aachen',
	)
	argparser.add_argument('-H', '--host', type=str, default='localhost', help='host to connect to')
	argparser.add_argument('-p', '--port', type=int, default='5559', help='port to connect to')

	try:
		args = argparser.parse_args()
	except IOError, msg:
		argparser.error(str(msg))

	main(args.host, args.port)

