import GCClient_Comms
import ConfigParser
import socket
import os
import sys
import platform
import json
import hashlib

class GCClient(object):
	def __init__(self):
		self.readConfig()
		
		self.uuid = self.school_name + "_" + socket.gethostname()
		#self.comms = GCClient_Comms.GCClient_Comms(gc_host = self.gc_host, userid = self.userid, password = self.password)
		
		#self.comms.publish(exchange_name = self.resp_exchange, routing_key=self.resp_key, message = json.dumps({'ClientID': self.uuid}, sort_keys=True))
		#self.comms.monitor(exchange_name = self.task_exchange, routing_key=self.task_key, callback = self.logging_callback)
		
		self.print_dict(self.generate_diagnostics())
		#loadModules();
		#start();
		
	def readConfig(self):
		config = ConfigParser.ConfigParser()
		config.readfp(open('gcclient.ini'))
		self.gc_host = config.get('DEFAULT', 'AMQP_HOST')
		self.userid = config.get('DEFAULT', 'USERID')
		self.password = config.get('DEFAULT', 'PASSWORD')
		self.resp_exchange = config.get('DEFAULT', 'RESP_EXCHANGE')
		self.resp_key = config.get('DEFAULT', 'RESP_KEY')
		self.task_exchange = config.get('DEFAULT', 'TASK_EXCHANGE')
		self.task_key = config.get('DEFAULT', 'TASK_KEY')
		self.school_name = config.get('DEFAULT', 'SCHOOLNAME')
	
	def logging_callback(self, ch, method, properties, body):
		print " [x] %r:%r" % (method.routing_key, body,)
	
	#def loadModules(self):
		
	
	#def start(self):
	def generate_diagnostics(self):
		diag_msg = {}
		diag_msg['OS'] = platform.platform() + " / " + platform.machine() + " - " + platform.processor()
		diag_msg['PythonVer'] = platform.python_version()
		diag_msg['uname'] = platform.uname()
		diag_msg['ClientID'] = self.uuid
		file_list = {}
		for file in os.listdir("."):
			if os.path.isfile(file):
				file_list[file] = hashlib.md5(open(file, 'rb').read()).hexdigest()
		
		diag_msg['Files'] = file_list
		return diag_msg
		
	def print_dict(self, dict):
		 for k, v in dict.iteritems():
			print k, ": ", v
			

gcclient = GCClient()