from GCClient import GCClient
import time

while True:
	try:
		instance = GCClient()
	finally:
		print "Reloading Client in 10sec"
		time.sleep(10)


