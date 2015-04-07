import pika
import time
import sys, traceback

class GCClient_Comms(object):
	def __init__(self, gc_host, userid, password):
		self.Running = True
		self.gc_host = gc_host
		self.creds = pika.credentials.PlainCredentials(username=userid, password=password)
		self.sslOptions = {'ca_certs':'client_certs/cacert.pem', 'certfile':'client_certs/test/alpha.test.bluenet.pem', 'keyfile': 'client_certs/test/alpha.test.bluenet.key.pem'}
		tries = 0
		success = False
		
		while (not success) and (tries < 5) and (self.Running == True):
			try:
				print "Attempting to connect publisher"
				
				self.resp_connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.gc_host, credentials=self.creds, port=5671, ssl=True, ssl_options=self.sslOptions))
				self.resp_channel = self.resp_connection.channel()
				
				success = True
			except:
				print "GCClient_Comms.__init__: Connection Error"
				traceback.print_exc(file=sys.stdout)
				tries = tries + 1
				time.sleep(5)
 
	def publish(self, exchange_name, routing_key, message, type='fanout'):
		print("Attempting to connect to " + self.gc_host)
		try:
			self.resp_channel.exchange_declare(exchange=exchange_name, type=type)
			self.resp_channel.basic_publish(exchange=exchange_name,
								  routing_key=routing_key,
								  body=message)
			
			print " [x] Sent %r:%r on exchange %r" % (routing_key, message, exchange_name)
		except:
			print "GCClient_Comms.publish: Connection Error"
			traceback.print_exc(file=sys.stdout)
			tries = tries + 1
			time.sleep(5)
	
	def quit(self):
		self.Running = False
		self.monitor_connection.close()
		self.resp_connection.close()
		
		
	def monitor(self, exchange_name, routing_keys, callback):
		tries = 0
		success = False
		
		while (not success) and (tries < 5) and (self.Running == True):
			try:
				self.monitor_connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.gc_host, credentials=self.creds, port=5671, ssl=True, ssl_options=self.sslOptions))
				channel = self.monitor_connection.channel()
				print "Listening on topic " + exchange_name + " with"
				channel.exchange_declare(exchange=exchange_name, type='topic')

				result = channel.queue_declare(exclusive=True)
				queue_name = result.method.queue
			
				for key in routing_keys:
					print "Binding to routing key %s" % key
					channel.queue_bind(exchange=exchange_name,
										queue=queue_name,
										routing_key=key)

				channel.basic_consume(callback,
										queue=queue_name,
										no_ack=True)

				channel.start_consuming()
				success=True
			except:
				print "GCClient_Comms.monitor: Connection Error"
				traceback.print_exc(file=sys.stdout)
				tries = tries + 1
				time.sleep(5)