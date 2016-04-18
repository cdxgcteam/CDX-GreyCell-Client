"""
File: GC_CModule_CambrionixMon.py
Description:
	Building a monitor and a query interface for Cambrionix Hubs.
	URL: http://www.cambrionix.com/downloads/cbrxapi/
	Based on their custom software and it requires a service to be running as well.
	Make sure the following packages are install before using Cambrionix Server (Ubuntu, anyway...):
	libc6:i386 libglib2.0-0:i386 libgtk2.0-0:i386 libicu52:i386 libncurses5:i386 libstdc++6:i386
ModuleID: cambrionixmon
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

# Cambrionix:
# import requests
# import numbers
# import pprint
from Cambrionix_JSONRPC_API import Cambrionix_JSONRPC_API, Cambrionix_JSONRPC_API_Exception

# For client module
from threading import Thread
import json
import queue
import logging
import pprint

# Setup Logging:
LoggerName = 'gcclient.module.'+__name__
logger = logging.getLogger(LoggerName)
logger.setLevel(logging.DEBUG)


class GC_CModule_CambrionixMon(GC_CModule):
	MODULE_ID = 'cambrionixmon'

	def __init__(self, gcclient):
		self.gcclient = gcclient
		logger.debug('Initialize Module: %s', self.MODULE_ID)

		# Running State
		self.Running = True

		self.cbrx_api = Cambrionix_JSONRPC_API()
		# Separate thread for running commands
		# self.thread = Thread(target=self.dockerMonitor)
		# self.thread.start()

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
