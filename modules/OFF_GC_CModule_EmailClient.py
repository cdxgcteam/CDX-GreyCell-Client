<<<<<<< HEAD:modules/OFF_GC_CModule_EmailClient.py
from GC_CModule import GC_CModule
import GC_Utility
import imaplib
import smtplib
from threading import Thread
import time
import email
import os
from email.mime.text import MIMEText
import logging

# Setup Logging:
LoggerName = 'gcclient.module.'+__name__
logger = logging.getLogger(LoggerName)
logger.setLevel(logging.DEBUG)

GC_EMAIL_POLL_INTERVAL = 60*1
GC_EMAIL_CONFIG_SMTP_SRV = "EMAIL.SMTPSRV"
GC_EMAIL_CONFIG_SMTP_PORT = "EMAIL.SMTPPORT"
GC_EMAIL_CONFIG_IMAP_SRV = "EMAIL.IMAPSRV"
GC_EMAIL_CONFIG_IMAP_PORT = "EMAIL.IMAPPORT"
GC_EMAIL_CONFIG_UNAME = "EMAIL.UNAME"
GC_EMAIL_CONFIG_PWORD = "EMAIL.PWORD"
GC_EMAIL_ATTACHMENT_DIR = "attachments"
GC_EMAIL_DEFAULT_USERNAME = "<username>"

class GC_CModule_EmailClient(GC_CModule):
	MODULE_ID = 'email'
	
	def __init__(self, gcclient):
		self.gcclient = gcclient
		logger.debug('Initialize Module: %s', self.MODULE_ID)
		
		# Pull in configuration items
		try :
			self.uname = self.gcclient.readConfigItem(GC_EMAIL_CONFIG_UNAME)
			self.pword = self.gcclient.readConfigItem(GC_EMAIL_CONFIG_PWORD)
			self.smtp_srv = self.gcclient.readConfigItem(GC_EMAIL_CONFIG_SMTP_SRV)
			self.smtp_port = self.gcclient.readConfigItem(GC_EMAIL_CONFIG_SMTP_PORT)
			self.imap_srv = self.gcclient.readConfigItem(GC_EMAIL_CONFIG_IMAP_SRV)
			self.imap_port = self.gcclient.readConfigItem(GC_EMAIL_CONFIG_IMAP_PORT)
		except Exception as e:
			#self.gcclient.log(GC_Utility.WARN, "Module Email Client unable to read configuration file! %s" % e)
			logger.warn('Module Email Client unable to read configuration file!', exc_info=True)
			raise AssertionError()
		
		if (self.uname == GC_EMAIL_DEFAULT_USERNAME):
			#self.gcclient.log(GC_Utility.WARN, "Email Client not configured!")
			logger.warn('Email Client not configured!', exc_info=True)
			raise AssertionError()
		
		try :
			#self.gcclient.log(GC_Utility.DEBUG, "EmailClient: Connecting to %s:%s" % (self.imap_srv, self.imap_port))
			logger.debug('EmailClient: Connecting to %s:%s' % (self.imap_srv, self.imap_port))
			self.mail = imaplib.IMAP4(host=self.imap_srv, port=self.imap_port)
			self.mail.login(self.uname, self.pword)	
			self.mail.select("inbox") # connect to inbox.
		except Exception as e:
			#self.gcclient.log(GC_Utility.WARN, "Module Email Client failed to create IMAP connection [%s]" % (e))
			#self.gcclient.log(GC_Utility.INFO, "Module Email Client failed to create IMAP connection [%s]" % (e))
			logger.warn('Module Email Client failed to create IMAP connection', exc_info=True)
			raise AssertionError()
			
		self.Running = True
		self.t = Thread(target=self.inboxPoll)
		self.t.start()

	""" 
	ModuleID: email
	Command Structure:
		cmd: String - sendmail
		msg: String - url to fetch 
		sender: String - email address of the sender
		receivers: Array of Strings - each recient
	
	Response Structure:
	startTime: String - ISO Date of task starting
	Title: String - Title of the page
	page_md5: String - MD5 of the page source
	links_md5: String - MD5 of all urls in the page, concatinated
	"""
	def handleTask(self, gccommand) :
		#self.gcclient.log(GC_Utility.DEBUG, "handleTask - [%s:%s] " % (gccommand[GC_Utility.GC_MODULEID], gccommand[GC_Utility.GC_TASKREF]) )
		logger.debug('handleTask - [%s:%s] ' % (gccommand[GC_Utility.GC_MODULEID], gccommand[GC_Utility.GC_TASKREF]))
		
		startTime =  GC_Utility.currentZuluDT()
		
		taskingObj = gccommand[GC_Utility.GC_CMD_DATA]
		
		response = {}
		response['startTime'] = startTime
		
		if (taskingObj['cmd'] == 'sendemail'):
			self.sendEmail(taskingObj['msg'], taskingObj['sender'], taskingObj['receivers'], gccommand[GC_Utility.GC_TASKREF] )
		
		#self.gcclient.log(GC_Utility.DEBUG, 'handleTask :: email :: Sending result...');
		logger.debug('email :: Sending result...')
		self.gcclient.sendResult(gccommand, response);
	
	def getModuleId(self):
		return self.MODULE_ID
	
	def quit(self):
		self.Running = False
		
	
	def inboxPoll(self):
		self.count = 0
		
		while self.Running:
			#self.gcclient.log(GC_Utility.DEBUG, 'emailClient : Polling imap server');
			logger.debug('emailClient : Polling imap server')
			self.mail.select()
			result, data = self.mail.search(None, '(UNSEEN)')

			ids = data[0] # data is a list.
			id_list = ids.split() # ids is a space separated string
			
			for num in id_list:
				result, data = self.mail.fetch(num, "(RFC822)") # fetch the email body (RFC822) for the given ID
				typ, data2 = self.mail.store(num,'+FLAGS','\\Seen')
	
				mail = email.message_from_string(data[0][1]) # here's the body, which is raw text of the whole email
				#self.gcclient.log(GC_Utility.INFO, "Received email subject %s" % mail['subject'])
				logger.info('Received email subject %s' % mail['subject'])
				response = {}

				response['cmd'] = 'receivedEmail'
				#response['msg'] = data[0][1]
				response['subject'] = mail['subject']
				
				# f = open('mail.txt', 'w')
				# f.write(data[0][1])
				# f.close()
				
				if mail.get_content_maintype() == 'multipart':
					#self.gcclient.log(GC_Utility.DEBUG, "Processing multipart email")
					logger.debug('Processing multipart email')
					
					for part in mail.walk():
						# multipart are just containers, so we skip them
						if part.get_content_maintype() == 'multipart':
							#self.gcclient.log(GC_Utility.DEBUG, "Nested Multipart")
							logger.debug('Nested Multipart')
							continue

						# is this part an attachment ?
						elif part.get('Content-Disposition') is None:
							#print part
							logger.debug('Part: '+part)
							#self.gcclient.log(GC_Utility.DEBUG, "Not a Content-Disposition")
							logger.debug('Not a Content-Disposition')
							continue
						
						# self.gcclient.log(GC_Utility.DEBUG, "Content-Disposition: %s" % part.get('Content-Disposition'))
						
						filename = part.get_filename()
						counter = 1
						#self.gcclient.log(GC_Utility.DEBUG, "Processing email attachment %s" % filename)
						logger.debug('Processing email attachment %s' % filename)
						
						# if there is no filename, we create one with a counter to avoid duplicates
						if not filename:
							filename = 'part-%03d%s' % (counter, 'bin')
							counter += 1

						att_path = os.path.join(GC_EMAIL_ATTACHMENT_DIR, filename)
						
						#Check if its already there
						if not os.path.isdir(GC_EMAIL_ATTACHMENT_DIR):
							#self.gcclient.log(GC_Utility.DEBUG, 'creating ' + GC_EMAIL_ATTACHMENT_DIR)
							logger.debug('creating ' + GC_EMAIL_ATTACHMENT_DIR)
							os.mkdir(GC_EMAIL_ATTACHMENT_DIR)
						elif os.path.isfile(att_path) :
							GC_Utility.handleBackup(att_path, self.gcclient)
						
						# finally write the stuff
						fp = open(att_path, 'wb')
						fp.write(part.get_payload(decode=True))
						fp.close()
				
				self.gcclient.sendOneOffResult(self.MODULE_ID, response)
				
			time.sleep(GC_EMAIL_POLL_INTERVAL)
	
	def sendEmail(self, emailbody, sender, receivers, taskRef):
		#self.gcclient.log(GC_Utility.INFO, 'sendEmail: [to %s from %s]' % (receivers, sender))
		logger.debug('sendEmail: [to %s from %s]' % (receivers, sender))
		# create a Message instance from the email data
		#message = email.message_from_string(emailbody)
		msg = MIMEText(emailbody)
		msg['From'] = sender
		msg['To'] = ', '.join(receivers)
		msg['Subject'] = "Task[" + taskRef + "]Task"
		self.doSMTP(sender, receivers, msg)
		
	def doSMTP(self, sender, receivers, msg):
		#self.gcclient.log(GC_Utility.INFO, 'doSMTP: [to %s from %s]' % (receivers, sender))
		logger.info('doSMTP: [to %s from %s]' % (receivers, sender))
		# open authenticated SMTP connection and send message with
		# specified envelope from and to addresses
		try:
			smtp = smtplib.SMTP(self.smtp_srv, self.smtp_port)
			smtp.starttls()
			smtp.login(self.uname, self.pword)
			smtp.sendmail(sender, [sender], msg.as_string())
			smtp.quit()
		except smtplib.SMTPException as e:
			#self.gcclient.log(GC_Utility.WARN, 'Caught SMTPException [%s]' % e)
			#self.gcclient.log(GC_Utility.INFO, 'Caught SMTPException [%s]' % e)
			logger.warn('Caught SMTPException', exc_info=True)
			
		
	def forwardEmail(self, emailId, to_list):
		# create a Message instance from the email data
		message = email.message_from_string(email_data)

		# replace headers (could do other processing here)
		message.replace_header("From", from_addr)
		message.replace_header("To", to_addr)

		# open authenticated SMTP connection and send message with
		# specified envelope from and to addresses
		smtp = smtplib.SMTP(self.smtp_srv, self.smtp_port)
		smtp.starttls()
		smtp.login(user, passwd)
		smtp.sendmail(from_addr, to_addr, message.as_string())
		smtp.quit()
=======
from GC_CModule import GC_CModule
import GC_Utility
import imaplib
import smtplib
from threading import Thread
import time
import email
import os
from email.mime.text import MIMEText
import logging

# Setup Logging:
LoggerName = 'gcclient.module.'+__name__
logger = logging.getLogger(LoggerName)
logger.setLevel(logging.DEBUG)

GC_EMAIL_POLL_INTERVAL = 60*1
GC_EMAIL_CONFIG_SMTP_SRV = "EMAIL.SMTPSRV"
GC_EMAIL_CONFIG_SMTP_PORT = "EMAIL.SMTPPORT"
GC_EMAIL_CONFIG_IMAP_SRV = "EMAIL.IMAPSRV"
GC_EMAIL_CONFIG_IMAP_PORT = "EMAIL.IMAPPORT"
GC_EMAIL_CONFIG_UNAME = "EMAIL.UNAME"
GC_EMAIL_CONFIG_PWORD = "EMAIL.PWORD"
GC_EMAIL_ATTACHMENT_DIR = "attachments"
GC_EMAIL_DEFAULT_USERNAME = "<username>"

class GC_CModule_EmailClient(GC_CModule):
	MODULE_ID = 'email'
	
	def __init__(self, gcclient):
		self.gcclient = gcclient
		logger.debug('Initialize Module: %s', self.MODULE_ID)
		
		# Pull in configuration items
		try :
			self.uname = self.gcclient.readConfigItem(GC_EMAIL_CONFIG_UNAME)
			self.pword = self.gcclient.readConfigItem(GC_EMAIL_CONFIG_PWORD)
			self.smtp_srv = self.gcclient.readConfigItem(GC_EMAIL_CONFIG_SMTP_SRV)
			self.smtp_port = self.gcclient.readConfigItem(GC_EMAIL_CONFIG_SMTP_PORT)
			self.imap_srv = self.gcclient.readConfigItem(GC_EMAIL_CONFIG_IMAP_SRV)
			self.imap_port = self.gcclient.readConfigItem(GC_EMAIL_CONFIG_IMAP_PORT)
		except Exception as e:
			#self.gcclient.log(GC_Utility.WARN, "Module Email Client unable to read configuration file! %s" % e)
			logger.warn('Module Email Client unable to read configuration file!', exc_info=True)
			raise AssertionError()
		
		if (self.uname == GC_EMAIL_DEFAULT_USERNAME):
			#self.gcclient.log(GC_Utility.WARN, "Email Client not configured!")
			logger.warn('Email Client not configured!', exc_info=True)
			raise AssertionError()
		
		try :
			#self.gcclient.log(GC_Utility.DEBUG, "EmailClient: Connecting to %s:%s" % (self.imap_srv, self.imap_port))
			logger.debug('EmailClient: Connecting to %s:%s' % (self.imap_srv, self.imap_port))
			self.mail = imaplib.IMAP4(host=self.imap_srv, port=self.imap_port)
			self.mail.login(self.uname, self.pword)	
			self.mail.select("inbox") # connect to inbox.
		except Exception as e:
			#self.gcclient.log(GC_Utility.WARN, "Module Email Client failed to create IMAP connection [%s]" % (e))
			#self.gcclient.log(GC_Utility.INFO, "Module Email Client failed to create IMAP connection [%s]" % (e))
			logger.warn('Module Email Client failed to create IMAP connection', exc_info=True)
			raise AssertionError()
			
		self.Running = True
		self.t = Thread(target=self.inboxPoll)
		self.t.start()

	""" 
	ModuleID: email
	Command Structure:
		cmd: String - sendmail
		msg: String - url to fetch 
		sender: String - email address of the sender
		receivers: Array of Strings - each recient
	
	Response Structure:
	startTime: String - ISO Date of task starting
	Title: String - Title of the page
	page_md5: String - MD5 of the page source
	links_md5: String - MD5 of all urls in the page, concatinated
	"""
	def handleTask(self, gccommand) :
		#self.gcclient.log(GC_Utility.DEBUG, "handleTask - [%s:%s] " % (gccommand[GC_Utility.GC_MODULEID], gccommand[GC_Utility.GC_TASKREF]) )
		logger.debug('handleTask - [%s:%s] ' % (gccommand[GC_Utility.GC_MODULEID], gccommand[GC_Utility.GC_TASKREF]))
		
		startTime =  GC_Utility.currentZuluDT()
		
		taskingObj = gccommand[GC_Utility.GC_CMD_DATA]
		
		response = {}
		response['startTime'] = startTime
		
		if (taskingObj['cmd'] == 'sendemail'):
			self.sendEmail(taskingObj['msg'], taskingObj['sender'], taskingObj['receivers'], gccommand[GC_Utility.GC_TASKREF] )
		
		#self.gcclient.log(GC_Utility.DEBUG, 'handleTask :: email :: Sending result...');
		logger.debug('email :: Sending result...')
		self.gcclient.sendResult(gccommand, response);
	
	def getModuleId(self):
		return self.MODULE_ID
	
	def quit(self):
		self.Running = False
		
	
	def inboxPoll(self):
		self.count = 0
		
		while self.Running:
			#self.gcclient.log(GC_Utility.DEBUG, 'emailClient : Polling imap server');
			logger.debug('emailClient : Polling imap server')
			self.mail.select()
			result, data = self.mail.search(None, '(UNSEEN)')

			ids = data[0] # data is a list.
			id_list = ids.split() # ids is a space separated string
			
			for num in id_list:
				result, data = self.mail.fetch(num, "(RFC822)") # fetch the email body (RFC822) for the given ID
				typ, data2 = self.mail.store(num,'+FLAGS','\\Seen')
	
				mail = email.message_from_string(data[0][1]) # here's the body, which is raw text of the whole email
				#self.gcclient.log(GC_Utility.INFO, "Received email subject %s" % mail['subject'])
				logger.info('Received email subject %s' % mail['subject'])
				response = {}

				response['cmd'] = 'receivedEmail'
				#response['msg'] = data[0][1]
				response['subject'] = mail['subject']
				
				# f = open('mail.txt', 'w')
				# f.write(data[0][1])
				# f.close()
				
				if mail.get_content_maintype() == 'multipart':
					#self.gcclient.log(GC_Utility.DEBUG, "Processing multipart email")
					logger.debug('Processing multipart email')
					
					for part in mail.walk():
						# multipart are just containers, so we skip them
						if part.get_content_maintype() == 'multipart':
							#self.gcclient.log(GC_Utility.DEBUG, "Nested Multipart")
							logger.debug('Nested Multipart')
							continue

						# is this part an attachment ?
						elif part.get('Content-Disposition') is None:
							#print part
							logger.debug('Part: '+part)
							#self.gcclient.log(GC_Utility.DEBUG, "Not a Content-Disposition")
							logger.debug('Not a Content-Disposition')
							continue
						
						# self.gcclient.log(GC_Utility.DEBUG, "Content-Disposition: %s" % part.get('Content-Disposition'))
						
						filename = part.get_filename()
						counter = 1
						#self.gcclient.log(GC_Utility.DEBUG, "Processing email attachment %s" % filename)
						logger.debug('Processing email attachment %s' % filename)
						
						# if there is no filename, we create one with a counter to avoid duplicates
						if not filename:
							filename = 'part-%03d%s' % (counter, 'bin')
							counter += 1

						att_path = os.path.join(GC_EMAIL_ATTACHMENT_DIR, filename)
						
						#Check if its already there
						if not os.path.isdir(GC_EMAIL_ATTACHMENT_DIR):
							#self.gcclient.log(GC_Utility.DEBUG, 'creating ' + GC_EMAIL_ATTACHMENT_DIR)
							logger.debug('creating ' + GC_EMAIL_ATTACHMENT_DIR)
							os.mkdir(GC_EMAIL_ATTACHMENT_DIR)
						elif os.path.isfile(att_path) :
							GC_Utility.handleBackup(att_path, self.gcclient)
						
						# finally write the stuff
						fp = open(att_path, 'wb')
						fp.write(part.get_payload(decode=True))
						fp.close()
				
				self.gcclient.sendOneOffResult(self.MODULE_ID, response)
				
			time.sleep(GC_EMAIL_POLL_INTERVAL)
	
	def sendEmail(self, emailbody, sender, receivers, taskRef):
		#self.gcclient.log(GC_Utility.INFO, 'sendEmail: [to %s from %s]' % (receivers, sender))
		logger.debug('sendEmail: [to %s from %s]' % (receivers, sender))
		# create a Message instance from the email data
		#message = email.message_from_string(emailbody)
		msg = MIMEText(emailbody)
		msg['From'] = sender
		msg['To'] = ', '.join(receivers)
		msg['Subject'] = "Task[" + taskRef + "]Task"
		self.doSMTP(sender, receivers, msg)
		
	def doSMTP(self, sender, receivers, msg):
		#self.gcclient.log(GC_Utility.INFO, 'doSMTP: [to %s from %s]' % (receivers, sender))
		logger.info('doSMTP: [to %s from %s]' % (receivers, sender))
		# open authenticated SMTP connection and send message with
		# specified envelope from and to addresses
		try:
			smtp = smtplib.SMTP(self.smtp_srv, self.smtp_port)
			smtp.starttls()
			smtp.login(self.uname, self.pword)
			smtp.sendmail(sender, [sender], msg.as_string())
			smtp.quit()
		except smtplib.SMTPException as e:
			#self.gcclient.log(GC_Utility.WARN, 'Caught SMTPException [%s]' % e)
			#self.gcclient.log(GC_Utility.INFO, 'Caught SMTPException [%s]' % e)
			logger.warn('Caught SMTPException', exc_info=True)
			
		
	def forwardEmail(self, emailId, to_list):
		# create a Message instance from the email data
		message = email.message_from_string(email_data)

		# replace headers (could do other processing here)
		message.replace_header("From", from_addr)
		message.replace_header("To", to_addr)

		# open authenticated SMTP connection and send message with
		# specified envelope from and to addresses
		smtp = smtplib.SMTP(self.smtp_srv, self.smtp_port)
		smtp.starttls()
		smtp.login(user, passwd)
		smtp.sendmail(from_addr, to_addr, message.as_string())
		smtp.quit()
>>>>>>> origin/master:GC_CModule_EmailClient.py
