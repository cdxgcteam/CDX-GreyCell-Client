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
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary

import subprocess
from threading import Thread
import queue

import hashlib
import re
import string
import logging

from html.parser import HTMLParser

# create a subclass to hash links
class CDXHTMLParser(HTMLParser):
    LinkString = ""

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            for name,value in attrs:
                if(name == 'href'):
                    self.LinkString = self.LinkString + value

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

# known file types to save, this will be used to prevent the save/open dialog in
# FF mp3 pdf  doc wmv tgz mov xbm xinc xls ppt eps exe rpm mpg bz2
GC_SELENIUM_SAVE_FILETYPES = ';'.join(['application/octet-stream',
                    'application/zip',
                    'application/x-zip',
                    'application/x-gzip',
                    'application/x-zip-compressed',
                    'application/x-msdownload',
                    'application/octet',
                    'application/x-shockwave-flash',
                    'application/x-ms-asx',
                    'application/tif',
                    'audio/x-wav',
                    'application/msword',
                    'application/x-rpm',
                    'application/msxls',
                    'audio/mpeg',
                    'application/pdf',
                    'image/tiff',
                    'video/x-ms-wmv',
                    'application/x-bzip2',
                    'video/quicktime'
                    'application/vnd.ms-powerpoint',
                    'video/mpeg',
                    'application/postscript'])


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

    # Start up the browser
    self.startFF()

    # Semaphore
    self.Running = True

    # Create a queue to buffer tasks
    self.queue = queue.Queue(maxsize=0)

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

      firefox_capabilities = DesiredCapabilities.FIREFOX
      firefox_capabilities["marionette"] = True

      # set the location to save files to
      if (platform.system() == 'Windows'):
        fp.set_preference("browser.download.dir", os.getcwd() + '\\' + GC_SELENIUM_SAVE_LOCATION)
      elif (platform.system() == 'Linux'):
        fp.set_preference("browser.download.dir", os.getcwd() + '/' + GC_SELENIUM_SAVE_LOCATION)
      #  firefox_capabilities["binary"] = "/usr/bin/firefox"

      logger.debug('Selenium Save File Types: %s', GC_SELENIUM_SAVE_FILETYPES)
      fp.set_preference("browser.helperApps.neverAsk.saveToDisk", GC_SELENIUM_SAVE_FILETYPES)

      # Since Selenium 3.0, can no longer get the process pid programatically.
      # Performing a diff of running FF processes instead.
      ff_pids_pre = self.findFFPIDs()

      # Initialize the selinium web driver
      self.driver = webdriver.Firefox(firefox_profile=fp, capabilities=firefox_capabilities)
      #self.driver = webdriver.Chrome()

      # Since Selenium 3.0, can no longer get the process pid programatically.
      # Performing a diff of running FF processes instead.
      ff_pids_post = self.findFFPIDs()

      # since some versions of FF spawn multiple processes, create comma seperated list
      ff_pids = ', '.join(list(set(ff_pids_post) - set(ff_pids_pre)))

      logger.info('Selenium Firefox started with PID ' + ff_pids)

      # Save the PID file
      f = open(GC_SELENIUM_PID_FILE, 'w')
      f.write(ff_pids)
      f.close()

    # Log exceptions and throw an AssertionError to notify the system that initialization failed.
    except Exception as e:
      logger.warn('Selenium failed to start Firefox!', exc_info=True)
      raise AssertionError()

  """
  Function: findFFPIDs
  Description: returns a list of all running firefox instances
  """
  def findFFPIDs(self):
    my_os = platform.system()
    pids = []

    # check to see if the process is running and is firefox.exe.
    try:
      if (my_os == 'Windows'):
        logger.debug("Attempting to find FF PIDS on " + my_os)
        taskList = subprocess.check_output('tasklist /NH /FI "ImageName eq firefox.exe"').decode('utf-8').strip().split("\n")
        if (taskList[0][0:4] != "INFO"):
          for task in taskList:
            pids.append(task.split()[1])

          logger.debug(taskList)

      elif (my_os == 'Linux'):
        taskList = subprocess.check_output("ps | grep firefox | cut -d ' ' -f1", shell=True).decode('utf-8').strip().split("\n")
        for task in taskList:
          pids.append(task)

        logger.debug(taskList)

      else:
        logger.warn('Unable to kill PID %s on platform %s' % (previous_pid, my_os), exc_info=True)

      # Remove the PID file when done
      os.remove(GC_SELENIUM_PID_FILE)
    except Exception as e:
      return pids

    return pids

  """
  Function: killPID
  Description: Looks for the designated pid file. If found, check to see if the process is still running. If still running, attempt to kill the process.
  The PID file would be left over if the GreyCell client crashed or was killed or closed manually

  New version handles comma seperated list in the pid file
  """
  def killPID(self):
    # Check to see if the PID file exists.
    if (os.path.isfile(GC_SELENIUM_PID_FILE)):

      my_os = platform.system()

      # since some versions of FF spawn multiple processes, the pid file may be a comma seperated list
      f = open(GC_SELENIUM_PID_FILE, 'r')
      previous_pids = f.read().split(',')
      f.close()

      for pid in previous_pids:
        # check to see if the process is running and is firefox.exe.
        try:
          if (my_os == 'Windows'):
            logger.debug("Attempting to kill FF on " + my_os)
            taskList = subprocess.check_output('tasklist /FI "PID eq %s"' % pid).decode('utf-8')
            logger.debug(taskList)

            if (taskList.find('firefox.exe') != -1):
              logger.info('Killing previous process with PID %s' % pid)
              subprocess.call('taskkill /PID %s' % pid)
          elif (my_os == 'Linux'):
            taskList = subprocess.check_output("ps -p %s" % pid, shell=True).decode('utf-8')

            if (taskList.find('firefox') != -1):
              logger.info('Killing previous process with PID %s' % pid)
              subprocess.call(['kill', '-9', pid])
          else:
            logger.warn('Unable to kill PID %s on platform %s' % (pid, my_os), exc_info=True)

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
    logger.debug('queuingTask - [%s:%s]' % (gccommand[GC_Utility.GC_MODULEID], gccommand[GC_Utility.GC_TASKREF]))

    self.queue.put(gccommand)

    logger.debug('queueStatus - [%s:%s tasks]' % (gccommand[GC_Utility.GC_MODULEID], self.queue.qsize()))

    # Log the queue size in 25 task increments
    if ((self.queue.qsize() % 25) == 0):
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

    logger.info('excuteCmd : [%s:%s(%s)]' % (gccommand[GC_Utility.GC_MODULEID], cmd, url))

    # Save off current title. Will look for a change in title after the page load.
    oldtitle = self.driver.title

    # Command the browser to load the URL
    self.driver.get(url)

    # increment the load counter
    self.loadCount = self.loadCount + 1

    # if over 200 urls have been loaded, restart the browser. This forces cleanup.
    if (self.loadCount > 100):
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
    parser = CDXHTMLParser()
    parser.feed(self.driver.page_source)

    response['links_md5'] = hashlib.md5(parser.LinkString.encode("utf-8")).hexdigest()

    # Reset the browser to a blank page
    self.driver.get('about:blank')

    logger.debug('sendResult :[%s:%s] ' % (gccommand[GC_Utility.GC_MODULEID], gccommand[GC_Utility.GC_TASKREF]))
    self.gcclient.sendResult(gccommand, response)
