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
from selenium.webdriver.support.ui import WebDriverWait 
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By



class GC_CModule_SeleniumTaskModule(GC_CModule):
	SELENIUM_LINUX_DEFAULT_PATH = './selenium-server-standalone-2.41.0.jar'
	SELENIUM_WINDOWS_DEFAULT_PATH = '.\\IEDriverServer.exe' #'.\\selenium-server-standalone-2.41.0.jar'
	BROWSERMOB_LINUX_DEFAULT_PATH = './browsermob/browsermob-proxy-2.0-beta-9/bin/browsermob-proxy'
	BROWSERMOB_WINDOWS_DEFAULT_PATH = '.\\browsermob\\browsermob-proxy-2.0-beta-9\\bin\\browsermob-proxy.bat'
	SELENIUM_HOST = 'localhost'
	SELENIUM_PORT = 4444
	BROWSERMOB_HOST = 'localhost'
	BROWSERMOB_PORT = 8080
	MODULE_ID = 'selenium'
	#SELENIUM_SERVER = null
	#SELENIUM_DRIVER = null

	def __init__(self, gcclient):
		self.gcclient = gcclient
		#self.BrowserMobPath = self.verifyBrowserMobPath('')
		self.SeleniumPath = self.verifySeleniumPath('')
		self.driver = self.makeDriver('firefox')
		
		#print 'BroweserMob ' + self.BrowserMobPath
		print 'SeleniumPath ' + self.SeleniumPath
		
	def quit(self):
		self.selenium_driver.quit()

	def getModuleId(self):
		return self.MODULE_ID

	def verifyBrowserMobPath(self, inputPath):
		browsermob_path = ''
		
		if inputPath != '':
			browsermob_path = inputPath;
		elif platform.platform() == 'Linux':
			browsermob_path = self.BROWSERMOB_LINUX_DEFAULT_PATH
		elif platform.platform() == 'Windows' :
			browsermob_path = self.BROWSERMOB_WINDOWS_DEFAULT_PATH
		
		if os.path.isfile(browsermob_path) :
			return browsermob_path
		else:
			raise Exception('Browsermod Proxy path does not exist...')
		
	def verifySeleniumPath(self, inputPath) :
		selenium_path = ''
		
		if inputPath != '' :
			selenium_path = inputPath
		elif platform.system() == 'Linux' :
			selenium_path = self.SELENIUM_LINUX_DEFAULT_PATH
		elif platform.system() == 'Windows' :
			selenium_path = self.SELENIUM_WINDOWS_DEFAULT_PATH
		
		print platform.system()
		
		if os.path.isfile(selenium_path) :
			return selenium_path
		else :
			raise Exception(TypeError, 'Selenium path does not exist...');

	def makeDriver(self, cmdr) :
		if (platform.system() == 'Windows') :
			if (cmdr == 'ie') :
				# IE Setup:
				portStr = '--port=4444' # + cmdr.sel_port;
				# TODO: Log when process returns... errors and non-errors
				#self.selenium_process = subprocess.Popen(['IEDriverServer.exe', portStr]);
				caps = DesiredCapabilities.INTERNETEXPLORER
				caps['ignoreProtectedModeSettings'] = True
				caps['browserName'] = 'internet explorer'
				caps['platform'] = 'WINDOWS'
				caps['INTRODUCE_FLAKINESS_BY_IGNORING_SECURITY_DOMAINS'] = True
				
				self.selenium_href = 'http://localhost:4444' #+ cmdr.sel_port;
				
				
				self.selenium_driver = webdriver.Ie(self.SELENIUM_WINDOWS_DEFAULT_PATH, caps)
				print "Web Driver Built"
				
			elif (cmdr == 'firefox') :
				# Selenium will have to be started MANUALLY!!!!...
				self.selenium_href = 'http://localhost:4444/wd/hub'
				self.selenium_driver = webdriver.Firefox()
		elif (platform.platform() == 'linux') : 
			if (cmdr.browser == 'firefox') :
				self.selenium_href = 'http://127.0.0.1:'+cmdr.sel_port+'/wd/hub';
				
				self.selenium_driver = webdriver.Builder().usingServer(serverAddress).withCapabilities(webdriver.Capabilities.firefox()).build()

	def handleTask(self, gccommand) :
		self.gcclient.log(1, "handleTask :: [x] " + gccommand[GC_Utility.GC_TASKREF] + ": ")#+ gccommand['command'])
		
		startTime =  GC_Utility.currentZuluDT()
		
		taskingObj = gccommand[GC_Utility.GC_CMD_DATA]
		
		response = {}
		response['startTime'] = startTime
		
		self.gcclient.log(1, 'handleTask :: Tasking Object:\n')#+util.inspect(taskingObj))

		#TODO Fix GCClient DEBUG Circular Dependency issue
		self.gcclient.log(1, 'handleTask :: execute_url :: Executing task...')
		
		oldtitle = self.selenium_driver.title
		
		self.selenium_driver.get(taskingObj['url'])
		timerstart = datetime.utcnow()
		time.sleep(taskingObj['timer'])
		
		while ((self.selenium_driver.title == oldtitle) or ((datetime.utcnow() - timerstart).seconds > 30)):
			print "Waiting for browser"
			time.sleep(5)
		
		if (self.selenium_driver.title == oldtitle):
			print "FAILURE!!!"
			
		response['Title'] = self.selenium_driver.title
		
		self.selenium_driver.get('about:blank')
		
		# try:
			# element = WebDriverWait(self.selenium_driver, 10).until(
				# EC.presence_of_element_located((By.ID, "Title"))
			# )
		# finally:
			# #self.selenium_driver.quit()
			# response['Title'] = self.selenium_driver.title
		# #self.selenium_driver.sleep(taskingObj['workTime'])
		
		
		self.gcclient.log(1, 'handleTask :: execute_url :: Sending result...');
		self.gcclient.sendResult(gccommand, response);

			

	def sendResult(self, amqpmsg, taskID, output, startTime) :
		result = {}
		result['taskID'] = taskID
		result['output'] = output
		result['executor'] = EXECUTOR
		result['os_platform'] = platform.uname()
		result['browser'] = cmdr.browser
		result['startTime'] = startTime
		result['endTime'] =  GC_Utility.currentZuluDT()
		result['elapsedTime'] = result['endTime'] - result['startTime']
		self.gcclient.log(result)
		
		# logger.debug('sendResult :: Result:\n'+util.inspect(result))

		#var message = JSON.stringify(result);
		# AMQP_CH.publish(AMQP_RESULTS_EXCHANGE, AMQP_RESULTS_ROUTING_KEY, new Buffer(message))
		# logger.debug("sendResult :: RESULT Sent!! :: %s:'%s'", AMQP_RESULTS_ROUTING_KEY, message)
		# AMQP_CH.ack(amqpmsg)

	# def start(self) :
		# // Start Driver:
		
		
		# return driver;
		# }).then(function (driver) {
				# SELENIUM_DRIVER = driver;
				# var amqpServerPath = 'amqp://'+cmdr.amqp_host+':'+cmdr.amqp_port;
				# logger.info('AMQP Path: '+amqpServerPath);
				# amqp.connect(amqpServerPath).then(function(conn) {
					# return when(conn.createChannel().then(function(ch) {
						# AMQP_CH = ch;
						# // Setup signals:
						# process.on('SIGINT', function () {
							# logger.info('SIGNAL: SIGINT caught: Closing connection.');
							# SELENIUM_DRIVER.quit();
							# AMQP_CH.close();
							# process.exit(1); // May need to kick out.
						# });
						
						# process.on('SIGTERM', function () {
							# logger.info('SIGNAL: SIGTERM caught: Closing connection.');
							# SELENIUM_DRIVER.quit();
							# AMQP_CH.close();
							# process.exit(1); // May need to kick out.
						# });
				
						# var tasks = ch.assertExchange(AMQP_TASK_EXCHANGE, 'topic', {durable: false});
						# tasks = tasks.then(function() {
							# logger.info('AMQP :: Tasks Exchange Asserted.');
							# return ch.assertQueue('', {exclusive: true});
						# });
				
						# tasks = tasks.then(function(qok) {
							# logger.info('AMQP :: Tasks Queue Asserted.');
							# var queue = qok.queue;
							# return all(AMQP_TASK_BINDING_KEYS.map(function(rk) {
								# ch.bindQueue(queue, AMQP_TASK_EXCHANGE, rk);
							# })).then(function() {
								# logger.info('AMQP :: Tasks Queues Binded.');
								# return queue;
							# });
						# });
						
						# tasks = tasks.then(function(queue) {
							# ch.prefetch(1);
							# return ch.consume(queue, handleTask, {noAck: false});
						# });
				
						# return tasks.then(function() {
							# logger.info(' AMQP :: Waiting for tasks. To exit press CTRL+C.');
						# });
					# }));
				# }).then(null, logger.warn);


# gctest = GC_CModule_SeleniumTaskModule(gcclient = GCClient.instance)

# taskObj = {}
# command = {}

# command['cmd'] = 'execute_url'
# command['url'] = 'https://www.google.com'
# command['workTime'] = 3600
# taskObj['TaskId'] = 'ABC123'
# taskObj[GCClient.GC_CLIENTID] = 'Client123'
# taskObj['routingKey'] = 'abc123'
# taskObj[GCClient.GC_CMD_DATA] = command
# taskObj[GCClient.GC_MODULEID] = 'selenium'
# taskObj[GCClient.GC_TASKREF] = 'Ref123'
# taskObj[GCClient.GC_RECEIVE_TIME] =  GC_Utility.currentZuluDT()
# time.sleep(5)

# gctest.handleTask(taskObj)

# taskObj = {}
# command = {}

# command['cmd'] = 'execute_url'
# command['url'] = 'https://www.cnn.com'
# command['workTime'] = 3600
# taskObj['TaskId'] = 'ABC123'
# taskObj[GCClient.GC_CLIENTID] = 'Client123'
# taskObj['routingKey'] = 'abc123'
# taskObj[GCClient.GC_CMD_DATA] = command
# taskObj[GCClient.GC_MODULEID] = 'selenium'
# taskObj[GCClient.GC_TASKREF] = 'Ref123'
# taskObj[GCClient.GC_RECEIVE_TIME] =  GC_Utility.currentZuluDT()

# time.sleep(5)

# gctest.handleTask(taskObj)