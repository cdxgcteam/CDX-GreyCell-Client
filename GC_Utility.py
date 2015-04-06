from datetime import datetime

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

def currentZuluDT():
	return datetime.utcnow().strftime(GC_DATESTR_FORMAT)[:19]

def print_dict(dict):
	 for k, v in dict.iteritems():
		print k, ": ", v
