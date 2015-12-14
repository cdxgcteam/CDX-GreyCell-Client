""" 
Filename: GC_CModule_Unzip.py
ModuleID: unzip

WARNING: THIS MODULE IS NOT FINISHED!!!

Command Structure:
cmd: String - currently 'execute_url'
url: String - url to fetch 
timer: int - time to wait for page load

Response Structure:
startTime: String - ISO Date of task starting
Title: String - Title of the page
page_md5: String - MD5 of the page source
links_md5: String - MD5 of all urls in the page, concatinated
"""

from GC_CModule import GC_CModule
import GC_Utility
import shlex
import time
import subprocess
import logging

# Setup Logging:
LoggerName = 'gcclient.module.'+__name__
logger = logging.getLogger(LoggerName)
logger.setLevel(logging.DEBUG)

class GC_CModule_Unzip(GC_CModule):
	MODULE_ID = 'unzip'
	
	def __init__(self, gcclient):
		self.gcclient = gcclient
		logger.debug('Initialize Module: %s', self.MODULE_ID)

	""" 
	ModuleID: unzip
	Command Structure:
		file: String - filename to unzip
		pass: String - password
	
	Response Structure:
		startTime: String - ISO Date of task starting
		stdout: String - Standard Out
		stderr: String - Standard Err
	"""
	def handleTask(self, gccommand) :
		#self.gcclient.log(GC_Utility.DEBUG, "handleTask - [%s:%s] " % (gccommand[GC_Utility.GC_MODULEID], gccommand[GC_Utility.GC_TASKREF]) )
		logger.debug('handleTask - [%s:%s]' % (gccommand[GC_Utility.GC_MODULEID], gccommand[GC_Utility.GC_TASKREF]))
		
		startTime =  GC_Utility.currentZuluDT()
		
		taskingObj = gccommand[GC_Utility.GC_CMD_DATA]
		
		response = {}
		response['startTime'] = startTime
		
		#self.gcclient.log(GC_Utility.DEBUG, 'execute: [%s for %s sec]' % (taskingObj['cmdline'], taskingObj['timer']))
		logger.debug('execute: [%s for %s sec]' % (taskingObj['cmdline'], taskingObj['timer']))
		
		stdout = ""
		waitTime = float(taskingObj['timer'])
		cmd = taskingObj['cmdline']
		
		try:
			p = subprocess.Popen(shlex.split(cmd), close_fds=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			time.sleep(waitTime)
		
			if (p.poll() is None):
				#self.gcclient.log(GC_Utility.WARN, 'Command [%s] did not terminate after %s. Killing...' % (cmd, waitTime))
				logger.warn('Command [%s] did not terminate after %s. Killing...' % (cmd, waitTime), exc_info=True)
				p.kill()
			
			response['stdout'] = p.stdout.read()
			response['stderr'] = p.stderr.read()
		except Exception as e:
			#self.gcclient.log(GC_Utility.WARN, 'Caught an exception while executing %s [%s]' % (cmd, e))
			logger.warn('Caught an exception while executing %s [%s]' % (cmd, e), exc_info=True)
		
		
		#self.gcclient.log(GC_Utility.DEBUG, 'execute : Sending result...');
		logger.debug('execute : Sending result...')
		self.gcclient.sendResult(gccommand, response);
	
	def getModuleId(self):
		return self.MODULE_ID
	
	def quit(self):
		return True
