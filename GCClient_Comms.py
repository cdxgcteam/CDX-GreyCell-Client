import pika
import time
import sys, traceback
import logging

# Setup Logging:
LoggerName = 'gcclient.'+__name__
logger = logging.getLogger(LoggerName)
logger.setLevel(logging.DEBUG)

GC_COMMS_AQMP_CERTFILE = 'AQMP_CERTFILE'
GC_COMMS_AQMP_KEYFILE  = 'AQMP_KEYFILE'
GC_COMMS_AQMP_CAFILE   = 'AQMP_CAFILE'

class GCClient_Comms(object):
	def __init__(self, gc_host, gc_port, userid, password, certfile, keyfile, cafile):
		self.Running = True
		self.gc_host = gc_host
		self.gc_port = int(gc_port)
		
		logger.debug("gc_host: %s" % self.gc_host)
		logger.debug("gc_port: %s" % self.gc_port)
		logger.debug("username: %s" % userid)
		logger.debug("cafile: %s" % cafile)
		logger.debug("certfile: %s" % certfile)
		logger.debug("keyfile: %s" % keyfile)

		self.creds = pika.credentials.PlainCredentials(username=userid, password=password)

		self.sslOptions = {'ca_certs':cafile, 'certfile':certfile, 'keyfile': keyfile}
		
		self.connect_publish()
 
	def publish(self, exchange_name, routing_key, message, type='fanout'):
		#print("Attempting to connect to " + self.gc_host)
		logger.info("Attempting to connect to " + self.gc_host)
		try:
			self.resp_channel.exchange_declare(exchange=exchange_name, type=type)
			self.resp_channel.basic_publish(exchange=exchange_name,
								  routing_key=routing_key,
								  body=message)
			
			#print " [x] Sent %r:%r on exchange %r" % (routing_key, message, exchange_name)
			logger.debug("[x] Sent %r:%r on exchange %r" % (routing_key, message, exchange_name))
		except:
			# print "GCClient_Comms.publish: Connection Error"
			# traceback.print_exc(file=sys.stdout)
			logger.warn("Connection Error", exc_info=True)
			self.connect_publish()
			
	def connect_publish(self):
		success = False
		tries = 0
		
		while (not success) and (tries < 5) and (self.Running == True):
			try:
				#print "Attempting to connect publisher"
				logger.info("Attempting to connect publisher")
				
				self.resp_connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.gc_host,
																						 credentials=self.creds,
																						 port=self.gc_port,
																						 ssl=True,
																						 ssl_options=self.sslOptions))

				self.resp_channel = self.resp_connection.channel()
				
				success = True
			except:
				# print "GCClient_Comms.__init__: Connection Error"
				# traceback.print_exc(file=sys.stdout)
				logger.warn("Connection Error", exc_info=True)
				tries = tries + 1
				time.sleep(5)

	def quit(self):
		if (self.Running):
			self.Running = False
			self.monitor_connection.close()
			self.resp_connection.close()
		
	def monitor(self, exchange_name, routing_keys, callback):
		tries = 0
		success = False
		
		while (not success) and (tries < 5) and (self.Running == True):
			try:
				self.monitor_connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.gc_host,
																							credentials=self.creds,
																							port=self.gc_port,
																							ssl=True,
																							ssl_options=self.sslOptions))

				channel = self.monitor_connection.channel()
				#print "Listening on topic " + exchange_name + " with"
				logger.info("Listening on topic " + exchange_name + " with")
				channel.exchange_declare(exchange=exchange_name, type='topic')

				result = channel.queue_declare(exclusive=True)
				queue_name = result.method.queue
			
				for key in routing_keys:
					#print "Binding to routing key %s" % key
					logger.info("Binding to routing key %s" % key)
					channel.queue_bind(exchange=exchange_name,
										queue=queue_name,
										routing_key=key)

				logger.info("basic_consume queue: %s" % queue_name)
				channel.basic_consume(callback,
										queue=queue_name,
										no_ack=True)

				logger.info("consumer starting...")
				channel.start_consuming()
				success=True
			except:
				# print "GCClient_Comms.monitor: Connection Error"
				# traceback.print_exc(file=sys.stdout)
				logger.warn("Connection Error", exc_info=True)
				tries = tries + 1
				time.sleep(5)
