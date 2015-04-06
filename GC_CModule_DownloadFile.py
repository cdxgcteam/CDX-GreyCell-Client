from GC_CModule import GC_CModule
import GC_Utility
import urllib2
import hashlib
import os
import shutil

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
		
		self.gcclient.log(GC_Utility.DEBUG, 'handleTask :: Tasking Object:\n')
		
		# Check for existing file, move it to back up
		self.handleBackup(taskingObj['saveas'])
		
		# Download the file
		try:
			f = urllib2.urlopen(taskingObj['url'])
			data = f.read()
			with open(taskingObj['saveas'], "wb") as code:
				code.write(data)
		
			# Send the file hash back
			response['MD5'] = hashlib.md5(open(taskingObj['saveas'], 'rb').read()).hexdigest()
		except urllib2.HTTPError as e:
			response['ERROR'] = "HTTP Error " + unicode(e.code)
		
		self.gcclient.log(GC_Utility.DEBUG, 'handleTask :: download :: Sending result...');
		self.gcclient.sendResult(gccommand, response);
	
	def getModuleId(self):
		return self.MODULE_ID
	
	def quit(self):
		return True
	
	# If filename already exists, move it to a backup directory
	# Create the backup directory if necessary
	# increment the filename as necessary
	def handleBackup(self, filename):
		if (os.path.isfile(filename)):
			(path, fname) = os.path.split(filename)
			(name, ext) = os.path.splitext(fname)
			backupdir = path+"\\backup"
			
			# Create the backup directory if necessary
			if (not os.path.isdir(backupdir)):
				self.gcclient.log(GC_Utility.DEBUG, 'GC_CModule_DownloadFile.handleBackup:: creating ' + backupdir)
				os.mkdir(backupdir)
			
			backupfile = backupdir + "\\" + name + ".bak"
			
			# increment the filename as necessary
			if(os.path.isfile(backupfile)):
				numbackups = 0
				backupfile = backupdir + "\\" + name + ".bak" + unicode(numbackups)
				
				while (os.path.isfile(backupfile)):
					numbackups = numbackups + 1
					backupfile = backupdir + "\\" + name + ".bak" + unicode(numbackups)
			
			# Moving the existing file to the backup dir
			self.gcclient.log(GC_Utility.INFO, 'GC_CModule_DownloadFile.handleBackup:: moving ' + filename + " to " + backupfile)
			shutil.move(filename, backupfile)
