import os
import platform
import subprocess
from GC_CModule import GC_CModule
import GC_Utility

from datetime import datetime
from datetime import timedelta
import time

from selenium import webdriver
from selenium.webdriver.common.keys import Keys

import subprocess
from threading import Thread
import Queue

import hashlib

GC_SELENIUM_POLL_INTERVAL = 5
GC_SELENIUM_PID_FILE = './selenium.pid'
GC_SELENIUM_EXECUTE_URL = 'execute_url'
GC_SELENIUM_DOWNLOAD_AND_EXEC = 'dl_execute'

class GC_CModule_SeleniumTaskModule(GC_CModule):
	MODULE_ID = 'selenium'

	def __init__(self, gcclient):
		self.gcclient = gcclient
		
		self.killPID()
		
		fp = webdriver.FirefoxProfile()

		fp.set_preference("browser.download.folderList",2)
		fp.set_preference("browser.download.manager.showWhenStarting",False)
		fp.set_preference("browser.download.dir", os.getcwd())
		fp.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/octet-stream")

		self.driver = self.selenium_driver = webdriver.Firefox(firefox_profile=fp)
		self.gcclient.log(GC_Utility.INFO, "Selenium Firefox started with PID %d" % self.driver.binary.process.pid)
		
		f = open(GC_SELENIUM_PID_FILE, 'w')
		f.write("%d" % self.driver.binary.process.pid)
		
		self.Running = True
		self.queue = Queue.Queue()
		self.thread = Thread(target=self.queuePollingThread)
		self.thread.start()
	
	def killPID(self):
		if (os.path.isfile(GC_SELENIUM_PID_FILE)):
			f = open(GC_SELENIUM_PID_FILE, 'r')
			previous_pid = f.read()
			f.close()
			os.remove(GC_SELENIUM_PID_FILE)
			
			# check to see if the process is running and is firefox.exe
			taskList = subprocess.check_output('tasklist /FI "PID eq %s"' % previous_pid)
			if (taskList.find('firefox.exe') != -1):
				self.gcclient.log(GC_Utility.INFO, "Killing previous process with PID %s" % previous_pid)
				subprocess.call('taskkill /PID %s' % previous_pid)

	def quit(self):
		self.Running = False
		self.thread.join()
		self.selenium_driver.quit()
		self.killPID()
		
	def getModuleId(self):
		return self.MODULE_ID


	def handleTask(self, gccommand) :
		self.gcclient.log(GC_Utility.DEBUG, "queuingTask - [%s:%s] " % (gccommand[GC_Utility.GC_MODULEID], gccommand[GC_Utility.GC_TASKREF]) )
		self.queue.put(gccommand)
		self.gcclient.log(GC_Utility.DEBUG, "queueStatus - [%s:%s tasks] " % (gccommand[GC_Utility.GC_MODULEID], self.queue.qsize() ))

	def execTask(self, gccommand):
		self.gcclient.log(GC_Utility.DEBUG, "handleTask - [%s:%s] " % (gccommand[GC_Utility.GC_MODULEID], gccommand[GC_Utility.GC_TASKREF]) )
		
		startTime =  GC_Utility.currentZuluDT()
		
		taskingObj = gccommand[GC_Utility.GC_CMD_DATA]
		
		response = {}
		response['startTime'] = startTime

		self.gcclient.log(GC_Utility.DEBUG, 'excuteCmd : [%s:%s(%s)]' % (gccommand[GC_Utility.GC_MODULEID], taskingObj['cmd'], taskingObj['url']))
		
		oldtitle = self.selenium_driver.title
		
		self.selenium_driver.get(taskingObj['url'])
		timerstart = datetime.utcnow()
		self.gcclient.log(GC_Utility.DEBUG, 'executeCmd : [%s pausing for %s sec]' % (gccommand[GC_Utility.GC_MODULEID], taskingObj['timer']))
		
		time.sleep(taskingObj['timer'])
		
		while ((self.selenium_driver.title == oldtitle) or ((datetime.utcnow() - timerstart).seconds > 30)):
			print "Waiting for browser"
			time.sleep(5)
		
		if (self.selenium_driver.title == oldtitle):
			print "FAILURE!!!"
			
		response['Title'] = self.selenium_driver.title
		response['page_md5'] = hashlib.md5(self.selenium_driver.page_source.encode("utf-8")).hexdigest()
		
		
		self.selenium_driver.get('about:blank')
		
		self.gcclient.log(GC_Utility.DEBUG, 'sendResult :[%s:%s] ' % (gccommand[GC_Utility.GC_MODULEID], gccommand[GC_Utility.GC_TASKREF]) )
		self.gcclient.sendResult(gccommand, response)

	def queuePollingThread(self):
		while self.Running:
			while not self.queue.empty():
				self.execTask(self.queue.get(False))
				
			time.sleep(GC_SELENIUM_POLL_INTERVAL)
