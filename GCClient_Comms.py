import pika
import time

class GCClient_Comms(object):
	def __init__(self, gc_host, userid, password):
		self.gc_host = gc_host
		self.creds = pika.credentials.PlainCredentials(username=userid, password=password)
		self.queue_exists = False

	def publish(self, exchange_name, routing_key, message):
		print("Attempting to connect to " + self.gc_host)
		
		tries = 0
		success = False
		while (not success) and (tries < 5):
			try:
				connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.gc_host, credentials=self.creds))
				channel = connection.channel()
				channel.queue_declare(queue='all.task');
				channel.exchange_declare(exchange=exchange_name, type='direct')
				
				channel.basic_publish(exchange=exchange_name,
									  routing_key=routing_key,
									  body=message)
									  
				print " [x] Sent %r:%r" % (routing_key, message)
				
				connection.close()
				success = True
			except:
				print "Connection Error"
				tries = tries + 1
				time.sleep(5)

	def monitor(self, exchange_name, routing_key, callback):
		tries = 0
		success = False
		while (not success) and (tries < 5):
			try:
				connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.gc_host, credentials=self.creds))
				channel = connection.channel()
				print "Listening on topic " + exchange_name + " with routingKey: " + routing_key
				channel.exchange_declare(exchange=exchange_name, type='topic')

				result = channel.queue_declare(exclusive=True)
				queue_name = result.method.queue

				binding_keys = routing_key
				
				channel.queue_declare(queue='queue.' + exchange_name)
				
				channel.queue_bind(exchange=exchange_name,
									queue='queue.' + exchange_name,
									routing_key=routing_key)

				channel.basic_consume(callback,
										queue='queue.' + exchange_name,
										no_ack=True)

				channel.start_consuming()
			except:
				print "Connection Error"
				tries = tries + 1
				time.sleep(5)