"""
Filename: GC_Utility.py
Description: Utility functions and static values
"""
from datetime import datetime
import os
import shutil
import subprocess
import logging

# Logging levels
DEBUG = 1
INFO = 2
WARN = 3

# Setup Logging:
LoggerName = 'gcclient.'+__name__
logger = logging.getLogger(LoggerName)
logger.setLevel(logging.DEBUG)

# Static strings
GC_CMD_INSTALL_MODULE = 1
GC_CMD_GEN_DEBUG = 2
GC_CLIENTID = 'ClientId'
GC_MODULEID = 'ModuleId'
GC_TASKREF = 'TaskRef'
GC_CMD_DATA = 'CommandData'
GC_RECEIVE_TIME = 'ReceiveTime'
GC_COMPLETE_TIME = 'CompleteTime'
GC_RESP_DATA = 'ResponseData'
GC_MOD_DIAG = 'RunDiag'
GC_MOD_PAUSE = 'Pause'
GC_MOD_QUIT = 'Quit'
GC_MOD_RELOAD = 'Reload'
GC_MOD_INSTALL = 'Install'
GC_MOD_DEBUG = 'debug'
GC_DATESTR_FORMAT = '%Y%m%dT%H%M%S.%f'
GC_LOG_DATETIME = 'datetime'
GC_LOG_MSG = 'msg'

"""
Function: currentZuluDT
Description: returns the current time in ISO format
"""
def currentZuluDT():
	return datetime.utcnow().isoformat()[:23]

"""
Function: print_dict
Description: Pretty print a dict data structure
"""
def print_dict(dict):
	for k, v in dict.iteritems():
		print("%s:%s", k, v)

"""
Function: handleBackup
Description: Handles backing up a file, if it exists.
 1. If filename already exists, move it to a backup directory
 2. Create the backup directory if necessary
 3. increment the filename as necessary
"""
def handleBackup(filename, gcclient):
	# If the file exists, 
	if (os.path.isfile(filename)):
		# extract file name, path 
		(path, fname) = os.path.split(filename)
		(name, ext) = os.path.splitext(fname)
		
		# Create backup directory name
		backupdir = path+"\\backup"
		
		# Create the backup directory if necessary
		if (not os.path.isdir(backupdir)):
			#gcclient.log(DEBUG, 'GC_CModule_DownloadFile.handleBackup:: creating ' + backupdir)
			logger.debug('creating ' + backupdir)
			os.mkdir(backupdir)
		
		# create the backup filename
		backupfile = backupdir + "\\" + name + ".bak"
		
		# increment the filename as necessary
		if(os.path.isfile(backupfile)):
			numbackups = 0
			backupfile = backupdir + "\\" + name + ".bak" + unicode(numbackups)
			
			# Keep incrementing until the file doesn't exist.
			while (os.path.isfile(backupfile)):
				numbackups = numbackups + 1
				backupfile = backupdir + "\\" + name + ".bak" + unicode(numbackups)
		
		# Moving the existing file to the backup dir
		#gcclient.log(INFO, 'GC_CModule_DownloadFile.handleBackup:: moving ' + filename + " to " + backupfile)
		logger.info('moving ' + filename + " to " + backupfile)
		shutil.move(filename, backupfile)


