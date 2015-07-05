#!/usr/bin/env python
# -*- coding: utf-8 -*-

import zmq
import argparse

def main(host, port, topic):
	context = zmq.Context.instance()
	publisher = context.socket(zmq.PUB)
	publisher.connect("tcp://{0}:{1}".format(host, port))

	running = True
	print("press [CTRL] + [D] to quit")
	while running:
		try:
			data = input("in> ")
		except EOFError:
			break
		publisher.send_multipart([topic.encode('utf-8'), data.encode('utf-8')])

	# clean up
	publisher.close()
	context.term()

if __name__ == "__main__":
	argparser = argparse.ArgumentParser(
		description='Test-Publisher for ZeroMQ bus system',
	)
	argparser.add_argument('-H', '--host', type=str, default='localhost', help='host to connect to')
	argparser.add_argument('-p', '--port', type=int, default='5559', help='port to connect to')
	argparser.add_argument('-t', '--topic', type=str, default='/test', help='topic used for communication')

	try:
		args = argparser.parse_args()
	except IOError as msg:
		argparser.error(str(msg))

	main(args.host, args.port, args.topic)

