#!/usr/bin/python
# -*- coding: utf-8 -*-

import zmq
import threading
import logging
import logging.handlers

class Logger(threading.Thread):
	"""logger for all messages and events"""
	def __init__(self, filename='bus.bz2'):
		super(Logger, self).__init__()
		self.filename = filename

		# receiving socket
		self.context = zmq.Context.instance()
		self.log_in = self.context.socket(zmq.PAIR)
		self.log_in.connect("inproc://logging")

		# logger parameters for stdout and compressed file
		log_format = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
		file_log_handler = logging.handlers.TimedRotatingFileHandler(self.filename, when='midnight', encoding='bz2', backupCount=7)
		file_log_handler.setFormatter(log_format)
		stream_log_handler = logging.StreamHandler()
		stream_log_handler.setFormatter(log_format)
		self.logger = logging.getLogger('logger')
		self.logger.setLevel(logging.INFO)
		self.logger.addHandler(file_log_handler)
		self.logger.addHandler(stream_log_handler)

	def run(self):
		while True:
			try:
				# receive message
				message = self.log_in.recv_multipart()

				if len(message) > 1:
					# message with content
					[topic, contents] = message
					self.logger.info("[msg] {%s} %s", topic, contents)
				else:
					# subscribe/unsubscribe
					message = message[0]
					topic = message[1:]
					if message[0] == '\x00':
						# unsubscribe
						self.logger.info("[unsub] {%s}", topic)
					elif message[0] == '\x01':
						# subscribe
						self.logger.info("[sub] {%s}", topic)
					else:
						self.logger.warning("[unknown message] %s", message)

			except zmq.ZMQError as e:
				if e.errno == zmq.ETERM:
					self.logger.error("socket error, stopped logging")
					break
				else:
					self.logger.error("unknown error occurred during logging")

def main():
	context = zmq.Context.instance()

	# socket facing clients
	frontend = context.socket(zmq.XSUB)
	frontend.bind("tcp://*:5559")

	# socket facing services
	backend = context.socket(zmq.XPUB)
	backend.bind("tcp://*:5560")

	# log socket
	log_out = context.socket(zmq.PAIR)
	log_out.bind("inproc://logging")

	# start logging thread
	logger = Logger()
	logger.start()

	try:
		zmq.proxy(frontend, backend, log_out)
	except KeyboardInterrupt:
		print "shutting down"
	finally:
		frontend.close()
		backend.close()
		logger.join()
		context.term()

if __name__ == "__main__":
	main()

