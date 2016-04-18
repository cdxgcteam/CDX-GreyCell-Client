"""
File: GC_CModule_DockerEventMon.py
Description:
	Based on this Gist: https://raw.githubusercontent.com/CyberInt/dockermon/master/dockermon.py
	Open sourced script.
ModuleID: dockereventmon
Command Structure:
	filter: String - change the filter used againt the docker event feed.
	filter_action: String - add, replace, delete, delete_all for the filters.

Response Structure:
	startTime: String - ISO Date of task starting
	MD5: String - MD5 of the downloaded file
	ERROR: String - Errors
"""
from GC_CModule import GC_CModule
import GC_Utility
# import urllib2
# import urllib.request, urllib.parse, urllib.error
# import hashlib
# import os
# import shutil
# import ssl
# import http.client


from contextlib import closing
from socket import socket, AF_UNIX
from subprocess import Popen, PIPE
from sys import version_info
import json

from threading import Thread
import queue
import pprint
import logging

# Setup Logging:
LoggerName = 'gcclient.module.'+__name__
logger = logging.getLogger(LoggerName)
logger.setLevel(logging.DEBUG)

if version_info[:2] < (3, 0):
	from httplib import OK as HTTP_OK
	from urlparse import urlparse
else:
	from http.client import OK as HTTP_OK
	from urllib.parse import urlparse

bufsize = 1024
default_sock_url = 'ipc:///var/run/docker.sock'


class DockermonError(Exception):
	pass

class GC_CModule_DockerEventMon(GC_CModule):
	MODULE_ID = 'dockereventmon'

	def __init__(self, gcclient):
		self.gcclient = gcclient
		logger.debug('Initialize Module: %s', self.MODULE_ID)

		# Running State
		self.Running = True

		# Separate thread for running commands
		self.thread = Thread(target=self.dockerMonitor, daemon=True)
		self.thread.start()

	def read_http_header(self, sock):
		"""Read HTTP header from socket, return header and rest of data."""
		buf = []
		hdr_end = '\r\n\r\n'

		while True:
			buf.append(sock.recv(bufsize).decode('utf-8'))
			data = ''.join(buf)
			i = data.find(hdr_end)
			if i == -1:
				continue
			return data[:i], data[i + len(hdr_end):]


	def header_status(self, header):
		"""Parse HTTP status line, return status (int) and reason."""
		status_line = header[:header.find('\r')]
		# 'HTTP/1.1 200 OK' -> (200, 'OK')
		fields = status_line.split(None, 2)
		return int(fields[1]), fields[2]


	def connect(self, url):
		"""Connect to UNIX or TCP socket.

			url can be either tcp://<host>:port or ipc://<path>
		"""
		url = urlparse(url)
		if url.scheme == 'tcp':
			sock = socket()
			netloc = tuple(url.netloc.rsplit(':', 1))
		elif url.scheme == 'ipc':
			sock = socket(AF_UNIX)
			netloc = url.path
		else:
			raise ValueError('unknown socket type: %s' % url.scheme)

		sock.connect(netloc)
		return sock

	#def dockerMonitor(self, callback, url=default_sock_url):
	def dockerMonitor(self, url=default_sock_url):
		"""Watch docker events. Will call callback with each new event (dict).

			url can be either tcp://<host>:port or ipc://<path>
		"""
		sock = self.connect(url)

		with closing(sock):
			sock.sendall(b'GET /events HTTP/1.1\n\n')
			header, payload = self.read_http_header(sock)
			status, reason = self.header_status(header)
			if status != HTTP_OK:
				raise DockermonError('bad HTTP status: %s %s' % (status, reason))

			# Messages are \r\n<size in hex><JSON payload>\r\n
			buf = [payload]
			while self.Running:
				chunk = sock.recv(bufsize)
				if not chunk:
					raise EOFError('socket closed')
				buf.append(chunk.decode('utf-8'))
				data = ''.join(buf)
				i = data.find('\r\n')
				if i == -1:
					continue

				size = int(data[:i], 16)
				start = i + 2  # Skip initial \r\n

				if len(data) < start + size + 2:
					continue
				payload = data[start:start+size]
				parsed_payload = json.loads(payload)
				logger.debug('Docker Event:\n%s' % pprint.pformat(parsed_payload))
				#callback(json.loads(payload))
				buf = [data[start+size+2:]]  # Skip \r\n suffix

	"""
	Function: handleTask
	Description: handle download commands
	"""
	def handleTask(self, gccommand):
		#self.gcclient.log(GC_Utility.DEBUG, 'downloadFile : Sending result...');
		logger.debug('Sending result...')
		self.gcclient.sendResult(gccommand, response);

	def getModuleId(self):
		return self.MODULE_ID

	def quit(self):
		self.Running = False
		#self.thread.join()
		return True
