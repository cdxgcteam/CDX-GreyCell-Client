import os
import platform
import subprocess
import datetime
import GCClient
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

class GC_CModule_SeleniumTaskModule():
	SELENIUM_LINUX_DEFAULT_PATH = './selenium-server-standalone-2.41.0.jar';
	SELENIUM_WINDOWS_DEFAULT_PATH = '.\\selenium-server-standalone-2.41.0.jar';
	BROWSERMOB_LINUX_DEFAULT_PATH = './browsermob/browsermob-proxy-2.0-beta-9/bin/browsermob-proxy';
	BROWSERMOB_WINDOWS_DEFAULT_PATH = '.\\browsermob\\browsermob-proxy-2.0-beta-9\\bin\\browsermob-proxy.bat';
	SELENIUM_HOST = 'localhost';
	SELENIUM_PORT = 4444;
	BROWSERMOB_HOST = 'localhost';
	BROWSERMOB_PORT = 8080;
	#SELENIUM_SERVER = null;
	#SELENIUM_DRIVER = null;

	def __init__(self, GCClient):
		self.GCClient = GCClient
		#self.BrowserMobPath = self.verifyBrowserMobPath('')
		self.SeleniumPath = self.verifySeleniumPath('')
		self.driver = self.makeDriver('ie')
		
		#print 'BroweserMob ' + self.BrowserMobPath
		print 'SeleniumPath ' + self.SeleniumPath
		
	def verifyBrowserMobPath(self, inputPath):
		browsermob_path = ''
		
		if inputPath != '':
			browsermob_path = inputPath;
		elif platform.platform() == 'Linux':
			browsermob_path = BROWSERMOB_LINUX_DEFAULT_PATH
		elif platform.platform() == 'Windows' :
			browsermob_path = BROWSERMOB_WINDOWS_DEFAULT_PATH
		
		if os.path.isfile(browsermob_path) :
			return browsermob_path
		else:
			raise Exception('Browsermod Proxy path does not exist...')
		
	def verifySeleniumPath(self, inputPath) :
		selenium_path = ''
		
		if inputPath != '' :
			selenium_path = inputPath
		elif platform.platform() == 'Linux' :
			selenium_path = SELENIUM_LINUX_DEFAULT_PATH
		elif platform.platform() == 'Windows' :
			selenium_path = SELENIUM_WINDOWS_DEFAULT_PATH
		
		if os.path.isfile(selenium_path) :
			return selenium_path
		else :
			raise Exception(TypeError, 'Selenium path does not exist...');

	def makeDriver(self, cmdr) :
		if (platform.platform() == 'win32') :
			if (cmdr == 'ie') :
				# IE Setup:
				portStr = '--port=' + cmdr.sel_port;
				# TODO: Log when process returns... errors and non-errors
				self.selenium_process = subprocess.Popen('IEDriverServer.exe', [portStr]);
				
				self.selenium_href = 'http://localhost:' + cmdr.sel_port;
				
				
				self.selenium_driver = webdriver.Builder().usingServer(serverAddress).withCapabilities({browserName: 'internet explorer', platform: 'WINDOWS',INTRODUCE_FLAKINESS_BY_IGNORING_SECURITY_DOMAINS: true}).build()
			#elif (cmdr.browser === 'firefox') :
				# Selenium will have to be started MANUALLY!!!!...
				#self.selenium_href = 'http://localhost:' + cmdr.sel_port + '/wd/hub'
				#self.selenium_driver = webdriver.Builder().
					#usingServer(serverAddress).
					#withCapabilities(webdriver.Capabilities.firefox()).
					#build()
		elif (platform.platform() == 'linux') : 
			if (cmdr.browser == 'firefox') :
				self.selenium_href = 'http://127.0.0.1:'+cmdr.sel_port+'/wd/hub';
				
				self.selenium_driver = webdriver.Builder().usingServer(serverAddress).withCapabilities(webdriver.Capabilities.firefox()).build()

	def handleTask(self, gccommand) :
		self.GCClient.log("handleTask :: [x] %s:'%s'", gccommand['routingKey'], gccommand['command'])
		
		startTime = datetime.utcnow()
		
		taskingObj = gccommand['command']
		
		response = {}
		response['TaskId'] = gccommand['TaskId']
		response['cmd'] = taskingObj['cmd']
		response['startTime'] = datetime.utcnow()
		
		self.GCClient.log(GCClient.DEBUG, 'handleTask :: Tasking Object:\n'+util.inspect(taskingObj))
		
		if (taskingObj['cmd'] == 'execute_url') :
			self.GCClient.log(GCClient.DEBUG, 'handleTask :: execute_url :: Executing task...')
			driver = SELENIUM_DRIVER
			self.selenium_driver.get(taskingObj['url'])
			self.selenium_driver.sleep(taskingObj['workTime'])
			title = self.selenium_driver.title
			self.GCClient.log(GCClient.DEBUG, 'handleTask :: execute_url :: Sending result...');
			GCClient.sendResult(gccommand, taskingObj['taskID'], title, startTime);
		elif (taskingObj.cmd == 'pause') :
			self.GCClient.log('handleTask :: Pausing for '+taskingObj.workTime+'ms. Will send message once timeout is reached.')
			# setTimeout(function () {
				# logger.info('handleTask :: Timeout Reached. Sending message.');
				# sendResult(msg, taskingObj.taskID, 'paused', startTime);
			# }, taskingObj.workTime);
		elif (taskingObj.cmd == 'quit') :
			self.GCClient.log('handleTask :: Quiting in '+QUIT_TIMEOUT+'ms. Will send message once quit timeout is reached.')
			self.GCClient.log('handleTask :: Quiting Timeout Reached. Sending message.');
			self.sendResult(msg, taskingObj.taskID, 'quit', startTime);
			self.selenium_process.kill
			

	def sendResult(self, amqpmsg, taskID, output, startTime) :
		result = {}
		result['taskID'] = taskID
		result['output'] = output
		result['executor'] = EXECUTOR
		result['os_platform'] = platform.uname()
		result['browser'] = cmdr.browser
		result['startTime'] = startTime
		result['endTime'] = Date.now()
		result['elapsedTime'] = result['endTime'] - result['startTime']
		self.GCClient.log(result)
		
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


