from GCClient import GCClient
import time

Running = True
while Running:
	try:
		if (is_changed(GCClient)):
			reload(GCClient)
			
		instance = GCClient()
		
		while instance.isRunning():
			time.sleep(30)
	except KeyboardInterrupt:
		print "Keyboard Interrupt"
		Running = False
		quit()
	except Exception as e:
		print e
	finally:
		instance.quit()
		print "Reloading Client in 10sec"
		time.sleep(10)


