#!/usr/bin/env python
# -*- coding: utf-8 -*-

import zmq
import threading
import logging
import logging.handlers
import util

class Logger(threading.Thread):
	"""logger for all messages and events"""
	def __init__(self, stop_logging, filename='bus.log'):
		super(Logger, self).__init__()
		self.filename = filename
		self.stop_logging = stop_logging

		# receiving socket
		self.context = zmq.Context.instance()
		self.log_in = self.context.socket(zmq.PAIR)
		self.log_in.connect("inproc://logging")
		self.log_in.setsockopt(zmq.RCVTIMEO, 1000)

		# logger parameters for stdout and compressed file
		log_format = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
		file_log_handler = util.TimedCompressingRotatingFileHandler(self.filename, when='midnight', backupCount=7)
		file_log_handler.setFormatter(log_format)
		stream_log_handler = logging.StreamHandler()
		stream_log_handler.setFormatter(log_format)
		self.logger = logging.getLogger('logger')
		self.logger.setLevel(logging.INFO)
		self.logger.addHandler(file_log_handler)
		self.logger.addHandler(stream_log_handler)

	def run(self):
		while not self.stop_logging.is_set():
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
					if message.startswith(b'\x00'):
						# unsubscribe
						self.logger.info("[unsub] {%s}", topic)
					elif message.startswith(b'\x01'):
						# subscribe
						self.logger.info("[sub] {%s}", topic)
					else:
						self.logger.warning("[unknown message] %s", message)

			except zmq.ZMQError as e:
				if e.errno == zmq.ETERM:
					self.logger.error("socket error, stopped logging")
					break
				elif e.errno == zmq.EAGAIN:
					pass
				else:
					print(e)
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
	stop_logging = threading.Event()
	logger = Logger(stop_logging)
	logger.start()

	try:
		zmq.proxy(frontend, backend, log_out)
	except KeyboardInterrupt:
		print("shutting down")
	finally:
		frontend.close()
		backend.close()
		stop_logging.set()
		logger.join()

if __name__ == "__main__":
	main()

