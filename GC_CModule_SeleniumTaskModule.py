""" 
Filename: GC_CModule_SeleniumTaskModule.py
ModuleID: selenium
Notes: This module runs in a thread

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
import re
import string
import logging

# Setup Logging:
LoggerName = 'gcclient.module.'+__name__
logger = logging.getLogger(LoggerName)
logger.setLevel(logging.DEBUG)

# Frequency in seconds for the queue
GC_SELENIUM_POLL_INTERVAL = 5
# file name of the lock file and process id storage location
GC_SELENIUM_PID_FILE = './selenium.pid'
# location to save files, relative to current directory
GC_SELENIUM_SAVE_LOCATION = 'attachments_2'

# static command strings
GC_SELENIUM_EXECUTE_URL = 'execute_url'
GC_SELENIUM_DOWNLOAD_AND_EXEC = 'dl_execute'

# known file types to save, this will be used to prevent the save/open dialog in FF
GC_SELENIUM_SAVE_FILETYPES_LIST = ['application/octet-stream',
							'application/zip',
							'application/x-zip',
							'application/x-zip-compressed',
							'application/x-msdownload',
							'application/octet',
							'application/x-shockwave-flash',
							'application/x-ms-asx']

GC_SELENIUM_SAVE_FILETYPES = string.join(GC_SELENIUM_SAVE_FILETYPES_LIST, ';')


class GC_CModule_SeleniumTaskModule(GC_CModule):
	# Static module ID string
	MODULE_ID = 'selenium'
	
	"""
	Function: init
	Description: Initializes the module starts FireFox/selenium and starts the thread/queue
	"""
	def __init__(self, gcclient):
		self.gcclient = gcclient
		logger.debug('Initialize Module: %s', self.MODULE_ID)

		# Clean up previous Firefox if the process is still running
		self.killPID()
				
		self.regex = re.compile('\.[html|htm|gif|jpeg|jpg|pdf|asp|shtm|shtml|tif|png|txt|xml|js|css|bmp|mht]')
		
		# Start up the browser
		self.startFF()
		
		# Semaphore
		self.Running = True
		
		# Create a queue to buffer tasks
		self.queue = Queue.Queue()
		
		# Separate thread for running commands
		self.thread = Thread(target=self.queuePollingThread)
		self.thread.start()
	
	"""
	Function: startFF
	Desription: Starts FF with a profile to automatically download known file types. Records the process id of the FF browser to 
	"""
	def startFF(self):
		self.loadCount = 0
		
		try:
			# Enable saving files
			fp = webdriver.FirefoxProfile()
			
			fp.set_preference("browser.download.folderList",2)
			fp.set_preference("browser.download.manager.showWhenStarting",False)
			
			# set the location to save files to
			if (platform.system() == 'Windows'):
				fp.set_preference("browser.download.dir", os.getcwd() + '\\' + GC_SELENIUM_SAVE_LOCATION)
			elif (platform.system() == 'Linux'):
				fp.set_preference("browser.download.dir", os.getcwd() + '/' + GC_SELENIUM_SAVE_LOCATION)
			
			logger.debug('Selenium Save File Types: %s', GC_SELENIUM_SAVE_FILETYPES)
			fp.set_preference("browser.helperApps.neverAsk.saveToDisk", GC_SELENIUM_SAVE_FILETYPES)
			
			# Initialize the selinium web driver
			self.driver = webdriver.Firefox(firefox_profile=fp)
			
			#self.gcclient.log(GC_Utility.INFO, "Selenium Firefox started with PID %d" % self.driver.binary.process.pid)
			logger.info('Selenium Firefox started with PID %d' % self.driver.binary.process.pid)
		
			# Save the PID file
			f = open(GC_SELENIUM_PID_FILE, 'w')
			f.write("%d" % self.driver.binary.process.pid)
			f.close()
		
		# Log exceptions and throw an AssertionError to notify the system that initialization failed.
		except Exception as e:
			#self.gcclient.log(GC_Utility.WARN, "Selenium failed to start Firefox! [%s]" % e)
			logger.warn('Selenium failed to start Firefox!', exc_info=True)
			raise AssertionError()
	
	"""
	Function: killPID
	Description: Looks for the designated pid file. If found, check to see if the process is still running. If still running, attempt to kill the process.
	The PID file would be left over if the GreyCell client crashed or was killed or closed manually
	"""
	def killPID(self):
		# Check to see if the PID file exists.
		if (os.path.isfile(GC_SELENIUM_PID_FILE)):
			my_os = platform.system()

			f = open(GC_SELENIUM_PID_FILE, 'r')
			previous_pid = f.read()
			f.close()
			
			# check to see if the process is running and is firefox.exe.
			try:
				if (my_os == 'Windows'):
					taskList = subprocess.check_output('tasklist /FI "PID eq %s"' % previous_pid)
					if (taskList.find('firefox.exe') != -1):
						#self.gcclient.log(GC_Utility.INFO, "Killing previous process with PID %s" % previous_pid)
						logger.info('Killing previous process with PID %s' % previous_pid)
						subprocess.call('taskkill /PID %s' % previous_pid)
				elif (my_os == 'Linux'):
					taskList = subprocess.check_output("ps -p %s" % previous_pid, shell=True)

					if (taskList.find('firefox') != -1):
						#self.gcclient.log(GC_Utility.INFO, "Killing previous process with PID %s" % previous_pid)
						logger.info('Killing previous process with PID %s' % previous_pid)
						subprocess.call(['kill', '-9', previous_pid])
				else:
					#self.gcclient.log(GC_Utility.WARN, 'Unable to kill PID %s on platform %s' % (previous_pid, my_os))
					logger.warn('Unable to kill PID %s on platform %s' % (previous_pid, my_os), exc_info=True)
				
				# Remove the PID file when done
				os.remove(GC_SELENIUM_PID_FILE)
			except Exception as e:
				return

	"""
	Function: quit
	Description: Cleanup thread, selenium and Firefox
	"""
	def quit(self):
		self.Running = False
		self.thread.join()
		self.driver.quit()
		self.killPID()
		
	def getModuleId(self):
		return self.MODULE_ID

	"""
	Function: handleTask
	Description: Accepts the command and puts the command into the queue. The thread will pull the task off in the order it arrived. Log the queue size in increments of 25
	"""
	def handleTask(self, gccommand) :
		#self.gcclient.log(GC_Utility.DEBUG, "queuingTask - [%s:%s] " % (gccommand[GC_Utility.GC_MODULEID], gccommand[GC_Utility.GC_TASKREF]) )
		logger.debug('queuingTask - [%s:%s]' % (gccommand[GC_Utility.GC_MODULEID], gccommand[GC_Utility.GC_TASKREF]))
		self.queue.put(gccommand)
		#self.gcclient.log(GC_Utility.DEBUG, "queueStatus - [%s:%s tasks] " % (gccommand[GC_Utility.GC_MODULEID], self.queue.qsize() ))
		logger.debug('queueStatus - [%s:%s tasks]' % (gccommand[GC_Utility.GC_MODULEID], self.queue.qsize()))
		
		# Log the queue size in 25 task increments
		if ((self.queue.qsize() % 25) == 0):
			#self.gcclient.log(GC_Utility.INFO, "Current Selenium Tasking Queue size is %s" % self.queue.qsize())
			logger.info('Current Selenium Tasking Queue size is %s' % self.queue.qsize())

	"""
	Function: queuePollingThread
	Description: Checks the queue for tasks and executes tasks in order
	"""
	def queuePollingThread(self):
		while self.Running:
			while not self.queue.empty() and self.Running:
				self.execTask(self.queue.get(False))
				
			time.sleep(GC_SELENIUM_POLL_INTERVAL)
	
	"""
	Function: execTask
	Description: Actually execute selenium tasks
	
	If enabled, restarts the browser every 200 page loads.
	
	1. Command browser to load url
	2. Wait defined amount of seconds
	3. gather evidence
	4. Reset browser back to about:blank
	"""
	def execTask(self, gccommand):
		#self.gcclient.log(GC_Utility.DEBUG, "handleTask - [%s:%s] " % (gccommand[GC_Utility.GC_MODULEID], gccommand[GC_Utility.GC_TASKREF]) )
		logger.debug('handleTask - [%s:%s]' % (gccommand[GC_Utility.GC_MODULEID], gccommand[GC_Utility.GC_TASKREF]))

		startTime =  GC_Utility.currentZuluDT()
		
		# Initialize local copies of the task
		taskingObj = gccommand[GC_Utility.GC_CMD_DATA]
		cmd = taskingObj['cmd']
		url = taskingObj['url']
		timer = taskingObj['timer']
		
		# Initialize response object
		response = {}
		response['startTime'] = startTime

		#self.gcclient.log(GC_Utility.INFO, 'excuteCmd : [%s:%s(%s)]' % (gccommand[GC_Utility.GC_MODULEID], cmd, url))
		logger.info('excuteCmd : [%s:%s(%s)]' % (gccommand[GC_Utility.GC_MODULEID], cmd, url))
		
		# Save off current title. Will look for a change in title after the page load.
		oldtitle = self.driver.title
		
		# Command the browser to load the URL
		self.driver.get(url)
		
		# increment the load counter
		self.loadCount = self.loadCount + 1
		
		# if over 200 urls have been loaded, restart the browser. This forces cleanup.
		if (self.loadCount > 200):
			self.driver.quit()
			self.killPID()
			self.startFF()
			
		#self.gcclient.log(GC_Utility.DEBUG, 'executeCmd : [%s pausing for %s sec]' % (gccommand[GC_Utility.GC_MODULEID], timer))
		logger.debug('executeCmd : [%s pausing for %s sec]' % (gccommand[GC_Utility.GC_MODULEID], timer))
		
		# Sleep for defined amount of seconds
		time.sleep(timer)
	
		# If the page title doesn't change, something went wrong
		if (self.driver.title == oldtitle):
			logger.warn('page title doesn\'t change, something went wrong')
			#print "FAILURE!!!"
		
		""" Gather scoring evidence """
		# Pulling the title of the page
		response['Title'] = self.driver.title
	
		# Hashing the whole page
		response['page_md5'] = hashlib.md5(self.driver.page_source.encode("utf-8")).hexdigest()
	
		# Hashing every link on the page
		elements = self.driver.find_elements_by_xpath("//a")
		hash_links = ""
	
		# parse the links, and hash them
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
		# f.write(self.driver.page_source.encode("utf-8"))
		# f.close()
		
		# Reset the browser to a blank page
		self.driver.get('about:blank')
		
		#self.gcclient.log(GC_Utility.DEBUG, 'sendResult :[%s:%s] ' % (gccommand[GC_Utility.GC_MODULEID], gccommand[GC_Utility.GC_TASKREF]) )
		logger.debug('sendResult :[%s:%s] ' % (gccommand[GC_Utility.GC_MODULEID], gccommand[GC_Utility.GC_TASKREF]))
		self.gcclient.sendResult(gccommand, response)


