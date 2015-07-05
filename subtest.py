#!/usr/bin/env python
# -*- coding: utf-8 -*-

import zmq
import argparse
import threading

def main(host, port, topic):
	context = zmq.Context.instance()
	subscriber = context.socket(zmq.SUB)
	subscriber.connect("tcp://{0}:{1}".format(host, port))
	subscriber.setsockopt_string(zmq.SUBSCRIBE, topic)

	print("quit with [CTRL] + [C]")
	try:
		while True:
			[address, contents] = subscriber.recv_multipart()
			print("[{0}] {1}".format(address, contents))
	except KeyboardInterrupt:
		pass
	finally:
		subscriber.close()
		context.term()

if __name__ == "__main__":
	argparser = argparse.ArgumentParser(
		description='Test-Publisher for ZeroMQ bus system',
	)
	argparser.add_argument('-H', '--host', type=str, default='localhost', help='host to connect to')
	argparser.add_argument('-p', '--port', type=int, default='5560', help='port to connect to')
	argparser.add_argument('-t', '--topic', type=str, default='/test', help='topic used for communication')

	try:
		args = argparser.parse_args()
	except IOError as msg:
		argparser.error(str(msg))

	main(args.host, args.port, args.topic)

