
class GC_CModule(object):
	def __init__(self, gcclient):
		raise NotImplementedError

	def handleTask(self, gccommand) :
		raise NotImplementedError
	
	def getModuleId(self):
		raise NotImplementedError
	
	def quit(self):
		raise NotImplementedError