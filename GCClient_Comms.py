import pika

class GCClient_Comms(object):
	def __init__(self, gc_host, userid, password):
		self.gc_host = gc_host
		self.creds = pika.credentials.PlainCredentials(username=userid, password=password)
		self.queue_exists = False

	def publish(self, exchange_name, routing_key, message):
		print("Attempting to connect to " + self.gc_host)
		
		connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.gc_host, credentials=self.creds))
		channel = connection.channel()
		channel.queue_declare(queue='all.task');
		channel.exchange_declare(exchange=exchange_name, type='direct')
		
		channel.basic_publish(exchange=exchange_name,
							  routing_key=routing_key,
							  body=message)
							  
		print " [x] Sent %r:%r" % (routing_key, message)
		
		connection.close()

	def monitor(self, exchange_name, routing_key, callback):
		connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.gc_host, credentials=self.creds))
		channel = connection.channel()

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