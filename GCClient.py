import GCClient_Comms
import GC_CModule
import ConfigParser
import socket
import os
import sys
import platform
import json
import hashlib
from datetime import datetime
from datetime import timedelta
import GC_Utility
import threading
import imp
import inspect
import subprocess
import inspect

instance = None
GC_AMQP_HOST = 'AMQP_HOST'
GC_USERID = 'USERID'
GC_PASSWORD = 'PASSWORD'
GC_RESP_EXCHANGE = 'RESP_EXCHANGE'
GC_RESP_KEY = 'RESP_KEY'
GC_LOG_EXCHANGE = 'LOG_EXCHANGE'
GC_LOG_KEY = 'LOG_KEY'
GC_TASK_EXCHANGE = 'TASK_EXCHANGE'
GC_TASK_KEY = 'TASK_KEY'
GC_SCHOOLNAME = 'SCHOOLNAME'
GC_CLIENTID = 'CLIENTID'
GC_CONFIG_CATEGORY = 'DEFAULT'
GC_ALL_TASKS = 'all.tasks'
GC_TASK_ROUTINGKEY = '.tasks'


class GCClient(object):
	ENABLE_COMMS = True
	PRINT_DEBUG = False
	SEND_DEBUG = False
	gc_modules = {}
	gc_threads = []
	
	def __init__(self, debug = False, enable_comms = True):
		self.Running = True
		self.PRINT_DEBUG = debug
		
		self.ENABLE_COMMS = enable_comms
		
		self.readConfig()
		
		GC_Utility.print_dict(self.generate_diagnostics())
		
		if self.ENABLE_COMMS:
			# Initialize Comms Module
			self.comms = GCClient_Comms.GCClient_Comms(gc_host = self.gc_host, userid = self.userid, password = self.password)

			# Start Listening to exchanges
			t = threading.Thread(name=GC_ALL_TASKS, target=self.comms.monitor, args=(self.task_exchange, [GC_ALL_TASKS, self.school_name + GC_TASK_ROUTINGKEY,  self.uuid + GC_TASK_ROUTINGKEY], self.logging_callback))
			t.start()
			self.gc_threads.append(t)
			
		self.loadModules()
		
	def isRunning(self):
		return self.Running
		
	def readConfig(self):
		config = ConfigParser.ConfigParser()
		config.readfp(open('gcclient.ini'))
		self.gc_host = config.get(GC_CONFIG_CATEGORY, GC_AMQP_HOST)
		self.userid = config.get(GC_CONFIG_CATEGORY, GC_USERID)
		self.password = config.get(GC_CONFIG_CATEGORY, GC_PASSWORD)
		self.resp_exchange = config.get(GC_CONFIG_CATEGORY, GC_RESP_EXCHANGE)
		self.resp_key = config.get(GC_CONFIG_CATEGORY, GC_RESP_KEY)
		self.log_exchange = config.get(GC_CONFIG_CATEGORY, GC_LOG_EXCHANGE)
		self.log_key = config.get(GC_CONFIG_CATEGORY, GC_LOG_KEY)
		self.task_exchange = config.get(GC_CONFIG_CATEGORY, GC_TASK_EXCHANGE)
		self.task_key = config.get(GC_CONFIG_CATEGORY, GC_TASK_KEY)
		self.school_name = config.get(GC_CONFIG_CATEGORY, GC_SCHOOLNAME)
		
		if (config.has_option(GC_CONFIG_CATEGORY, GC_CLIENTID)):
			self.clientid = config.get(GC_CONFIG_CATEGORY, GC_CLIENTID)
		else:
			self.clientid = socket.gethostname()
		
		self.uuid = self.school_name + "_" + self.clientid
	
	def readConfigItem(self, configItem):
		config = ConfigParser.ConfigParser()
		config.readfp(open('gcclient.ini'))

		return config.get(GC_CONFIG_CATEGORY, configItem)
		
	
	def loadModules(self):
		# Add built in functions to the gc_modules dictionary`
		self.gc_modules[GC_Utility.GC_MOD_DIAG] = self.run_diag
		self.gc_modules[GC_Utility.GC_MOD_QUIT] = self.quit
		
		# Walk the current directory and load any file GC_CModule_*.py
		for file in os.listdir("."):
			(path, name) = os.path.split(file)
			(name, ext) = os.path.splitext(name)
			
			# Check that this is a file with a name GC_CModule_*.py
			if os.path.isfile(file) and name.startswith('GC_CModule_') and ext == '.py':
				
				# Load the module
				self.loadModule(file)


	def quit(self) :
		# Shutting down modules
		for name in self.gc_modules:
			m = self.gc_modules[name]
			if not inspect.ismethod(m):
				self.log(GC_Utility.INFO, "Shutting down " + m.getModuleId())
				m.quit()
		
		# Turn off AMQP
		if self.ENABLE_COMMS:
			self.comms.quit()

		self.Running = False


	def logging_callback(self, ch, method, properties, body):
		if self.ENABLE_COMMS:
			self.log(GC_Utility.DEBUG, "Received msg") #method.routing_key)
		
		# 2. TaskCreateDT: String (YYYYMMDDZHHMMSS.SSS) <withheld><br>
		# 3. ModuleID: Integer Associated with command module<br>
		# 4. TaskRef: Integer defined by module<br>
		# 5. CommandData: Key Value array, defined by module<br>
		rcvd_task = json.loads(body)
		rcvd_task[GC_Utility.GC_CLIENTID] = self.uuid
		
		GC_Utility.print_dict(rcvd_task[GC_Utility.GC_CMD_DATA])
		
		rcvd_task[GC_Utility.GC_RECEIVE_TIME] = GC_Utility.currentZuluDT()
		create_time = datetime.strptime(rcvd_task[GC_Utility.GC_RECEIVE_TIME], GC_Utility.GC_DATESTR_FORMAT)
		
		# Figure out which module... key/value pair on moduleid with objects....
		if rcvd_task[GC_Utility.GC_MODULEID] in self.gc_modules:
			# Check create time + 5min
			# TODO: use create time!!
			if (datetime.utcnow() - create_time)  < timedelta(seconds=(60*5)):
				try:
					self.gc_modules[rcvd_task[GC_Utility.GC_MODULEID]].handleTask(rcvd_task)
				except Exception as e:
					self.log(GC_Utility.WARN, "GCClient.logging_callback caught exception %s" % e)
			else:
				self.log(GC_Utility.INFO, rcvd_task[GC_Utility.GC_TASK_ID] + " create time > 5 min old ")
		else:
			self.log(GC_Utility.INFO, rcvd_task[GC_Utility.GC_MODULEID] + " not found in ")
			#self.log(GC_Utility.DEBUG, self.gc_modules.keys())

	def sendResult(self, taskObj, respData):
		# 2. ModuleID: Integer Associated with command module<br>
		# 3. TaskRef: Integer defined by module<br>
		# 4. RecieveTime: String (YYYYMMDDZHHMMSS.SSS) <br>
		# 5. CompleteTime: String (YYYYMMDDZHHMMSS.SSS) <br>
		# 6. ResponseData: Key Value array, defined by module<br>
		
		taskObj[GC_Utility.GC_COMPLETE_TIME] = GC_Utility.currentZuluDT()
		taskObj[GC_Utility.GC_RESP_DATA] = respData
		del taskObj[GC_Utility.GC_CMD_DATA]
		GC_Utility.print_dict(taskObj)
		
		if self.ENABLE_COMMS:
			self.comms.publish(exchange_name = self.resp_exchange, routing_key=self.resp_key, message = json.dumps(taskObj))
	
	def sendOneOffResult(self, moduleId, respData):
		# 2. ModuleID: Integer Associated with command module<br>
		# 3. TaskRef: Integer defined by module<br>
		# 4. RecieveTime: String (YYYYMMDDZHHMMSS.SSS) <br>
		# 5. CompleteTime: String (YYYYMMDDZHHMMSS.SSS) <br>
		# 6. ResponseData: Key Value array, defined by module<br>
		taskObj = []
		taskObj[GC_Utility.GC_MODULEID] = moduleId
		taskObj[GC_Utility.GC_COMPLETE_TIME] = GC_Utility.currentZuluDT()
		taskObj[GC_Utility.GC_RESP_DATA] = respData
		
		GC_Utility.print_dict(taskObj)
		
		if self.ENABLE_COMMS:
			self.comms.publish(exchange_name = self.resp_exchange, routing_key=self.resp_key, message = json.dumps(taskObj))

	def log(self, log_level, msg):
		log_msg = {}
		log_msg[GC_Utility.GC_LOG_DATETIME] = GC_Utility.currentZuluDT()
		log_msg[GC_Utility.GC_CLIENTID] = self.uuid
		log_msg[GC_Utility.GC_LOG_MSG] = msg
		
		curframe = inspect.currentframe()
		calframe = inspect.getouterframes(curframe, 2)

		
		log_msg['caller'] = "%s:%s:%s" % (calframe[1][1], calframe[1][3], calframe[1][2])
		
		if (log_level == GC_Utility.DEBUG):
			log_msg['level'] = "DEBUG" 
		elif (log_level == GC_Utility.WARN):
			log_msg['level'] = "WARNING"
		else:
			log_msg['level'] = "INFO"
			
		
		if self.ENABLE_COMMS:
			self.comms.publish(exchange_name = self.log_exchange, routing_key=self.log_key, type='direct', message = json.dumps(log_msg))
		else:
			print log_msg
			
	def run_diag(gcclient, taskObj):
		if (taskObj[GC_Utility.GC_MODULEID] == GC_Utility.GC_MOD_DIAG) :
			GCClient.getInstance().sendResponse(taskObj = taskObj, respData = generate_diagnostics)
		else:
			raise Exception('Invalid ModuleID')

	def generate_diagnostics(self):
		diag_msg = {}
		diag_msg['OS'] = platform.platform() + " / " + platform.machine() + " - " + platform.processor()
		diag_msg['PythonVer'] = platform.python_version()
		diag_msg['uname'] = platform.uname()
		file_list = {}
		for file in os.listdir("."):
			if os.path.isfile(file):
				file_list[file] = hashlib.md5(open(file, 'rb').read()).hexdigest()
		
		diag_msg['Files'] = file_list
		if (platform.system() == 'Windows'):
			diag_msg['processList'] = subprocess.check_output('tasklist')
		elif (platform.system() == 'Linux'):
			diag_msg['processList'] = subprocess.check_output('ps', '-l')
		else:
			diag_msg['processList'] = "Error retrieving process list on platform %s" % platform.system()
			
		return diag_msg

	def loadModule(self, filename):
		(path, name) = os.path.split(filename)
		(name, ext) = os.path.splitext(name)
		
		# Check that this is a file exists
		if os.path.isfile(filename) and ext == '.py':
			
			# Load the module
			(f, filename, data) = imp.find_module(name, [path])
			module = imp.load_module(name, f, filename, data)
			
			# Check module for a GC_CModule class
			for name in dir(module):
				obj = getattr(module, name)
				
				# Check module for a GC_CModule subclass, and not GC_CModule
				if name != 'GC_CModule' and inspect.isclass(obj) and issubclass(obj, GC_CModule.GC_CModule):
					# Load the module, and add it to the gc_modules dictionary
					try: 
						self.log(GC_Utility.DEBUG, "Loading GC_CModule: " + obj.__name__)
						m = obj(self)
						self.gc_modules[m.getModuleId()] = m
						self.log(GC_Utility.INFO, "Loaded Module: " + m.getModuleId())
					except AssertionError:
						self.log(GC_Utility.WARN, "Failed to load module %s" % (name))
		
	# def reloadModule(self, moduleid):
		# m = self.gc_modules[moduleid]
		
		# if not inspect.ismethod(m):
			# mod_class = m.__class__
			# cname = m.__name__
			# m.quit()
			# reload(cname)
			

		