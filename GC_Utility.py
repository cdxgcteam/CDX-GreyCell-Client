from datetime import datetime
import os
import shutil

DEBUG = 1
INFO = 2
WARN = 3

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
GC_DATESTR_FORMAT = '%Y%m%dZ%H%M%S.%f'
GC_LOG_DATETIME = 'datetime'
GC_LOG_MSG = 'msg'

def currentZuluDT():
	return datetime.utcnow().strftime(GC_DATESTR_FORMAT)[:19]

def print_dict(dict):
	 for k, v in dict.iteritems():
		print k, ": ", v

# If filename already exists, move it to a backup directory
# Create the backup directory if necessary
# increment the filename as necessary
def handleBackup(filename, gcclient):
	if (os.path.isfile(filename)):
		(path, fname) = os.path.split(filename)
		(name, ext) = os.path.splitext(fname)
		backupdir = path+"\\backup"
		
		# Create the backup directory if necessary
		if (not os.path.isdir(backupdir)):
			gcclient.log(DEBUG, 'GC_CModule_DownloadFile.handleBackup:: creating ' + backupdir)
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
		gcclient.log(INFO, 'GC_CModule_DownloadFile.handleBackup:: moving ' + filename + " to " + backupfile)
		shutil.move(filename, backupfile)