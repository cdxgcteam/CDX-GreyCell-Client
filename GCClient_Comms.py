# Pika specific
import pika
from pika import exceptions

# Other Libs:
import time
import sys, traceback
import logging
<<<<<<< HEAD
import pprint
import re
import socket

# Setup Logging:
LoggerName = 'gcclient.'+__name__
logger = logging.getLogger(LoggerName)
logger.setLevel(logging.DEBUG)

=======

# Setup Logging:
LoggerName = 'gcclient.'+__name__
logger = logging.getLogger(LoggerName)
logger.setLevel(logging.DEBUG)

>>>>>>> origin/master
GC_COMMS_AQMP_CERTFILE = 'AQMP_CERTFILE'
GC_COMMS_AQMP_KEYFILE  = 'AQMP_KEYFILE'
GC_COMMS_AQMP_CAFILE   = 'AQMP_CAFILE'

class GCClient_Comms(object):
<<<<<<< HEAD
    def __init__(self, gc_host, gc_port, userid, password, certfile, keyfile, cafile, resp_exchange, mon_exchange, mon_routing_key, mon_callback, resp_type='fanout', mon_type='topic'):
        self.Running = True
        self.gc_host = gc_host
        self.gc_port = int(gc_port)
        self.gc_core_channel = None

        logger.debug("gc_host: %s" % self.gc_host)
        logger.debug("gc_port: %s" % self.gc_port)
        logger.debug("username: %s" % userid)
        logger.debug("cafile: %s" % cafile)
        logger.debug("certfile: %s" % certfile)
        logger.debug("resp_exchange: %s" % resp_exchange)
        logger.debug("resp_type: %s" % resp_type)
        logger.debug("mon_exchange: %s" % mon_exchange)
        logger.debug("mon_type: %s" % mon_type)
        logger.debug("mon_routing_key: %s" % mon_routing_key)
        #logger.debug("mon_callback: %o" % mon_callback)

        self.response_exchange = resp_exchange
        self.response_type = resp_type
        self.monitor_exchange = mon_exchange
        self.monitor_type = mon_type
        self.monitor_routing_key = mon_routing_key
        self.monitor_callback = mon_callback

        self.creds = pika.credentials.PlainCredentials(username=userid, password=password)

        self.sslOptions = {'ca_certs':cafile, 'certfile':certfile, 'keyfile': keyfile}
        
        self.parameters = pika.ConnectionParameters(host=self.gc_host,
                                             credentials=self.creds,
                                             heartbeat_interval=30,
                                             port=self.gc_port,
                                             ssl=False,
                                             ssl_options=self.sslOptions)
	
        #self.initiate_connection()

    def publish(self, routing_key, message):
        logger.info("Attempting to publish to " + self.gc_host)
        try:
            #self.resp_channel.exchange_declare(exchange=exchange_name, type=type)
            self.resp_channel.basic_publish(exchange=self.response_exchange,
                                  routing_key=routing_key,
                                  body=message)

            logger.debug("[x] Sent %r:%r on exchange %r" % (routing_key, message, self.response_exchange))
        except:
            logger.warn("Connection Error", exc_info=False)
            tries = 0
            success = False
        
            logger.info('reinitializing publish connection')
            
            while (not success) and (tries < 5) and (self.Running == True):
                try:
                    logger.info("Creating response connection and channel")
                    self.resp_connection = pika.BlockingConnection(self.parameters)          
                    self.resp_channel = self.resp_connection.channel()
                    self.resp_channel.basic_publish(exchange=self.response_exchange,
                                  routing_key=routing_key,
                                  body=message)

                    logger.debug("[x] Sent %r:%r on exchange %r" % (routing_key, message, self.response_exchange))
                    success = True        
                except Exception as e:
                    logger.debug(e)
                    logger.warn("Connection Error", exc_info=True)
                    tries = tries + 1
                    time.sleep(5)

    def initiate_connection(self):
        while (self.Running == True):
            tries = 0
            success = False
	
            logger.debug('entered initiate_connection')
            while (not success) and (tries < 5) and (self.Running == True):
                try:
                    logger.info("Creating response connection and channel")
                    self.resp_connection = pika.BlockingConnection(self.parameters)          
                    self.resp_channel = self.resp_connection.channel()
                    success = True        
                except Exception as e:
                    logger.debug(e)
                    logger.warn("Connection Error", exc_info=True)
                    tries = tries + 1
                    time.sleep(5)
            
            if (success):
                tries = 0
                success = False
                logger.debug('parameters: %r' % pprint.pformat(self.parameters))
            
                while (not success) and (tries < 5) and (self.Running == True):
                    try:
                        logger.info("Creating monitor connection and channel")
                        self.monitor_connection = pika.BlockingConnection(self.parameters)          
                
                        self.monitor_channel = self.monitor_connection.channel()
                        success=True
                    except Exception as e:
                        logger.debug(e)
                        logger.warn("Connection Error", exc_info=True)
                        tries = tries + 1
                        time.sleep(5)
                        
            if (success):
                self.monitor()


    def execute_connection(self, connection):
        channel_resp = yield connection.channel()
        logger.info("Response Channel Created")

        self.resp_channel = channel_resp
        channel_resp.exchange_declare(exchange=self.response_exchange, type=self.response_type)
        logger.info("Response Exchange Declared")

        channel = yield connection.channel()
        logger.info("Monitor Channel Created")

        # Save the channel
        self.gc_core_channel = channel
        # var AMQP_RESULTS_EXCHANGE = 'fanout.cdxresults';
        # var AMQP_RESULTS_ROUTING_KEY = 'tasks.results';
        # var AMQP_RESULTS_QUEUE = 'queue.'+AMQP_RESULTS_EXCHANGE+'.cdxserver';
        exchange = yield channel.exchange_declare(exchange=self.monitor_exchange, type=self.monitor_type)
        logger.info("Monitor Exchange Created")

        queue = yield channel.queue_declare(exclusive=True)
        logger.info("Monitor Queue Declared")
        self.monitor_queue_name = queue.method.queue

        logger.debug("exchange %r :: queue_name %r :: routing_key %r" % (self.monitor_exchange, self.monitor_queue_name, self.monitor_routing_key))
        if isinstance(self.monitor_routing_key, list):
            for routing_key in self.monitor_routing_key:
                yield channel.queue_bind(exchange=self.monitor_exchange,queue=self.monitor_queue_name,routing_key=routing_key)
                logger.debug("loop - Queue Bound with routing_key: %r" % routing_key)
        else:
            yield channel.queue_bind(exchange=self.monitor_exchange,queue=self.monitor_queue_name,routing_key=self.monitor_routing_key)
            logger.debug("Queue Bound with routing_key: %r" % self.monitor_routing_key)
        logger.info("Monitor Queue Bound Completed")

        queue_object, consumer_tag = yield channel.basic_consume(queue=self.monitor_queue_name,no_ack=True)
        logger.debug('queue_object: %r' % queue_object)
        logger.debug('consumer_tag: %r' % consumer_tag)

        l = task.LoopingCall(self.monitor_callback, queue_object)
        logger.info("Monitor Looping Call Started for Twisted")
        l.start(0.01)

    # This is a tester function for the Twisted code for pika:
    def read(self, queue_object):

        ch,method,properties,body = yield queue_object.get()

        if body:
            logger.debug(body)

        #yield ch.basic_ack(delivery_tag=method.delivery_tag)

    def quit(self):
        if (self.Running):
            self.Running = False
            self.monitor_connection.close()
            self.resp_connection.close()

    def monitor(self):
        tries = 0
        success = False
        logger.debug('parameters: %r' % pprint.pformat(self.parameters))
        
        while (not success) and (tries < 5) and (self.Running == True):
            try:
                logger.info("Listening on topic " + self.monitor_exchange + " with")
                self.monitor_channel.exchange_declare(exchange=self.monitor_exchange, type='topic')
        
                result = self.monitor_channel.queue_declare(exclusive=True)
                queue_name = result.method.queue
                
                for key in self.monitor_routing_key:
                    logger.info("Binding to routing key %s" % key)
                    self.monitor_channel.queue_bind(exchange=self.monitor_exchange,
                                        queue=queue_name,
                                        routing_key=key)
        
                logger.info("basic_consume queue: %s" % queue_name)
                self.monitor_channel.basic_consume(self.monitor_callback,
                                        queue=queue_name,
                                        no_ack=True)
        
                logger.info("consumer starting...")
                self.monitor_channel.start_consuming()
                success=True
            except Exception as e:
                logger.debug(e)
                logger.warn("Connection Error", exc_info=True)
                tries = tries + 1
                time.sleep(5)
=======
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
>>>>>>> origin/master
