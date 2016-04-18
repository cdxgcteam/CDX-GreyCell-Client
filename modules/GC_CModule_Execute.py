""" 
Filename: GC_CModule_Execute.py
ModuleID: execute
Command Structure:
	cmdline: String - command to execute
	timer: int - number of seconds to wait for command to execute

Response Structure:
	startTime: String - ISO Date of task starting
	stdout: String - Standard Out
	stderr: String - Standard Err
"""

from GC_CModule import GC_CModule
import GC_Utility
import shlex
import time
import subprocess
import platform
import logging

# Setup Logging:
LoggerName = 'gcclient.module.'+__name__
logger = logging.getLogger(LoggerName)
logger.setLevel(logging.DEBUG)

class GC_CModule_Execute(GC_CModule):
	MODULE_ID = 'execute'
	
	def __init__(self, gcclient):
		self.gcclient = gcclient
		logger.debug('Initialize Module: %s v2', self.MODULE_ID)

	def handleTask(self, gccommand) :
		#self.gcclient.log(GC_Utility.DEBUG, "handleTask - [%s:%s] " % (gccommand[GC_Utility.GC_MODULEID], gccommand[GC_Utility.GC_TASKREF]) )
		logger.debug('handleTask - [%s:%s]' % (gccommand[GC_Utility.GC_MODULEID], gccommand[GC_Utility.GC_TASKREF]))
		
		# Initialize response
		startTime =  GC_Utility.currentZuluDT()
		response = {}
		response['startTime'] = startTime
		
		# Initialize local variables
		taskingObj = gccommand[GC_Utility.GC_CMD_DATA]
		waitTime = float(taskingObj['timer'])
		cmd = taskingObj['cmdline']
		
		#self.gcclient.log(GC_Utility.DEBUG, 'execute: [%s for %s sec]' % (taskingObj['cmdline'], taskingObj['timer']))
		logger.debug('execute: [%s for %s sec]' % (taskingObj['cmdline'], taskingObj['timer']))
		
		try:
			# Execute the command
			p = subprocess.check_call(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=waitTime)
			
			
			# Record stderr and stderr to the response
			response['stdout'] = p.stdout.read()
			response['stderr'] = p.stderr.read()
			
		# Catch and log any errors
		except Exception as e:
			#self.gcclient.log(GC_Utility.WARN, 'Caught an exception while executing %s [%s]' % (cmd, e))
			logger.warn('Caught an exception while executing %s' % (cmd), exc_info=True)
		
		self.gcclient.sendResult(gccommand, response);
	
	def getModuleId(self):
		return self.MODULE_ID
	
	def quit(self):
		return True
