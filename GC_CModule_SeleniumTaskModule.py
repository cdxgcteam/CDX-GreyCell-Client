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
		
		# Enable saving files
		fp = webdriver.FirefoxProfile()

		fp.set_preference("browser.download.folderList",2)
		fp.set_preference("browser.download.manager.showWhenStarting",False)
		fp.set_preference("browser.download.dir", os.getcwd())
		fp.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/octet-stream")

		self.driver = self.selenium_driver = webdriver.Firefox(firefox_profile=fp)
		self.gcclient.log(GC_Utility.INFO, "Selenium Firefox started with PID %d" % self.driver.binary.process.pid)
		
		f = open(GC_SELENIUM_PID_FILE, 'w')
		f.write("%d" % self.driver.binary.process.pid)
		f.close()

		self.Running = True
		self.queue = Queue.Queue()
		self.thread = Thread(target=self.queuePollingThread)
		self.thread.start()
	
	def killPID(self):
		if (os.path.isfile(GC_SELENIUM_PID_FILE)):
			my_os = platform.system()

			f = open(GC_SELENIUM_PID_FILE, 'r')
			previous_pid = f.read()
			f.close()
			
			# check to see if the process is running and is firefox.exe
			try:
                                if (my_os == 'Windows'):
					taskList = subprocess.check_output('tasklist /FI "PID eq %s"' % previous_pid)
					if (taskList.find('firefox.exe') != -1):
						self.gcclient.log(GC_Utility.INFO, "Killing previous process with PID %s" % previous_pid)
						subprocess.call('taskkill /PID %s' % previous_pid)
				elif (my_os == 'Linux'):
					print "ps -p %s" % previous_pid
					taskList = subprocess.check_output("ps -p %s" % previous_pid, shell=True)
					print "Linux Tasklist [%s]" % taskList

					if (taskList.find('firefox') != -1):
						self.gcclient.log(GC_Utility.INFO, "Killing previous process with PID %s" % previous_pid)
						subprocess.call(['kill', '-9', previous_pid])
				else:
					self.gcclient.log(GC_Utility.WARN, 'Unable to kill PID %s on platform %s' % (previous_pid, my_os))
			
				os.remove(GC_SELENIUM_PID_FILE)
			except Exception as e:
				return

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
		
		# Pulling the title of the page
		response['Title'] = self.selenium_driver.title
		
		# Hashing the whole page
		response['page_md5'] = hashlib.md5(self.selenium_driver.page_source.encode("utf-8")).hexdigest()
		
		# Hashing every link on the page
		elements = self.selenium_driver.find_elements_by_xpath("//a")
		hash_links = ""
		
		for link in elements:
			try:
				if str(link.get_attribute("href"))[0:4] == "http":
					hash_links = hash_links + str(link.get_attribute("href"))
					#print str(link.get_attribute("href"))
			except StaleElementReferenceException:
				pass
		
		response['links_md5'] = hashlib.md5(hash_links).hexdigest()
		
		# Diagnostics for figuring what source is being provided back.
		# f = open('./%s.html' % gccommand[GC_Utility.GC_TASKREF], 'w')
		# f.write(self.selenium_driver.page_source.encode("utf-8"))
		# f.close()
		
		self.selenium_driver.get('about:blank')
		
		self.gcclient.log(GC_Utility.DEBUG, 'sendResult :[%s:%s] ' % (gccommand[GC_Utility.GC_MODULEID], gccommand[GC_Utility.GC_TASKREF]) )
		self.gcclient.sendResult(gccommand, response)

	def queuePollingThread(self):
		while self.Running:
			while not self.queue.empty() and self.Running:
				self.execTask(self.queue.get(False))
				
			time.sleep(GC_SELENIUM_POLL_INTERVAL)
