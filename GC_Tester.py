from GCClient import GCClient
import GC_Utility
import json
import time
import traceback
import sys

try:
	instance = GCClient(debug = True, enable_comms = False)

	taskObj = {}
	command = {}
	urls = ['http://www.navy.mil/media/audio/17 APRIL NEWCASTweb.mp3',
			'http://www.navy.mil/media/allhands/acrobat/AH200705.pdf',
			'http://www.navy.mil/media/allhands/flash/AH200701.1.html',
			'http://www.navy.mil/media/allhands/flash/AH200701/ahcover.swf',
			'http://www.navy.mil/media/OtherMedia/YearInReview2006/soundslider.swf_size=1',
			'http://www.navy.mil/media/OtherMedia/YearInReview2006/U.S. Navy Year in Review 2006.zip',
			'http://www.navy.mil/media/video/features/cno_special/cno_message_hurricane2_060619.asx',
			'http://www.afmc.af.mil/photos/media_email.asp_id=4631.html',
			'http://www.afmc.af.mil/photos/media_email.asp_id=17325.html',
			'http://www.afmc.af.mil/photos/index.asp_galleryID=2317&page=1.html',
			'http://www.afmc.af.mil/photos/media_email.asp_id=24841.html',
			'http://www.afmc.af.mil/photos/media_email.asp_id=22046.html',
			'http://www.afmc.af.mil/photos/media_email.asp_id=35926.html',
			'http://www.afmc.af.mil/photos/media_email.asp_id=78908.html',
			'http://www.afmc.af.mil/photos/media_email.asp_id=29206.html',
			'http://www.afmc.af.mil/photos/media_email.asp_id=98589.html',
			'http://www.afmc.af.mil/photos/media_email.asp_id=33946.html',
			'http://www.afmc.af.mil/photos/media_email.asp_id=17680.html',
			'http://www.afmc.af.mil/photos/index.asp_galleryID=408.html',
			'http://www.afmc.af.mil/photos/media_email.asp_id=28424.html',
			'http://www.afmc.af.mil/photos/media_email.asp_id=7076.html',
			'http://www.afmc.af.mil/photos/media_email.asp_id=22348.html',
			'http://www.afmc.af.mil/photos/media_email.asp_id=10230.html',
			'http://www.afmc.af.mil/photos/media_email.asp_id=16074.html',
			'http://www.afmc.af.mil/photos/index.asp_galleryID=372&page=1.html',
			'http://www.afmc.af.mil/photos/media_email.asp_id=9819.html',
			'http://www.afmc.af.mil/photos/media_email.asp_id=8057.html',
			'http://www.afmc.af.mil/photos/media_email.asp_id=15784.html',
			'http://www.afmc.af.mil/photos/media_email.asp_id=29263.html',
			'http://www.afmc.af.mil/photos/media_email.asp_id=23095.html',
			'http://www.afmc.af.mil/photos/index.asp_galleryID=441.html',
			'http://www.afmc.af.mil/photos/media_email.asp_id=31911.html',
			'http://www.afmc.af.mil/photos/media_email.asp_id=6871.html',
			'http://www.afmc.af.mil/photos/media_email.asp_id=94292.html',
			'http://www.afmc.af.mil/photos/media_email.asp_id=632.html',
			'http://www.afmc.af.mil/photos/index.asp_galleryID=2795.html',
			'http://www.afmc.af.mil/photos/media_email.asp_id=17724.html',
			'http://www.afmc.af.mil/photos/media_email.asp_id=18407.html',
			'http://www.afmc.af.mil/photos/media_email.asp_id=7329.html',
			'http://www.afmc.af.mil/photos/media_email.asp_id=36044.html',
			'http://www.afmc.af.mil/photos/media_email.asp_id=4506.html',
			'http://www.afmc.af.mil/photos/index.asp_galleryID=356&page=1.html',
			'http://www.afmc.af.mil/photos/media_email.asp_id=78435.html',
			'http://www.afmc.af.mil/photos/media_email.asp_id=60281.html',
			'http://www.afmc.af.mil/photos/index.asp_galleryID=370.html',
			'http://www.afmc.af.mil/photos/media_email.asp_id=58314.html',
			'http://www.afmc.af.mil/photos/index.asp_page=12.html',
			'http://www.afmc.af.mil/photos/index.asp_galleryID=372.html',
			'http://www.afmc.af.mil/photos/media_email.asp_id=36962.html',
			'http://www.afmc.af.mil/photos/media_email.asp_id=60271.html',
			'http://www.afmc.af.mil/photos/media_email.asp_id=23916.html',
			'http://www.afmc.af.mil/photos/media_email.asp_id=79362.html',
			'http://www.afmc.af.mil/photos/media_email.asp_id=15477.html',
			'http://www.afmc.af.mil/photos/index.asp_galleryID=357&page=2.html',
			'http://www.afmc.af.mil/photos/media_email.asp_id=76318.html',
			'http://www.afmc.af.mil/photos/media_email.asp_id=37990.html',
			'http://www.afmc.af.mil/photos/media_email.asp_id=18406.html',
			'http://www.afmc.af.mil/photos/media_email.asp_id=28506.html',
			'http://www.afmc.af.mil/photos/media_email.asp_id=28422.html',
			'http://www.afmc.af.mil/photos/media_email.asp_id=92687.html',
			'http://www.afmc.af.mil/photos/media_email.asp_id=60625.html',
			'http://www.afmc.af.mil/photos/media_email.asp_id=105206.html',
			'http://www.afmc.af.mil/photos/media_email.asp_id=27686.html',
			'http://www.afmc.af.mil/photos/media_email.asp_id=97704.html',
			'http://www.afmc.af.mil/photos/media_email.asp_id=57223.html',
			'http://www.afmc.af.mil/photos/media_email.asp_id=23733.html',
			'http://www.afmc.af.mil/photos/media_email.asp_id=62190.html',
			'http://www.afmc.af.mil/photos/media_email.asp_id=24103.html',
			'http://www.afmc.af.mil/photos/media_email.asp_id=60599.html',
			'http://www.afmc.af.mil/photos/media_email.asp_id=36491.html',
			'http://www.afmc.af.mil/photos/media_email.asp_id=523.html',
			'http://www.afmc.af.mil/photos/media_email.asp_id=18186.html',
			'http://www.afmc.af.mil/photos/media_email.asp_id=25440.html',
			'http://www.afmc.af.mil/photos/media_email.asp_id=12386.html',
			'http://www.afmc.af.mil/photos/media_email.asp_id=11889.html',
			'http://www.afmc.af.mil/photos/media_email.asp_id=82515.html',
			'http://www.afmc.af.mil/photos/index.asp_galleryID=389.html',
			'http://www.afmc.af.mil/photos/media_email.asp_id=10189.html',
			'http://www.afmc.af.mil/photos/media_email.asp_id=62354.html',
			'http://www.afmc.af.mil/photos/media_email.asp_id=26464.html']
			
	taskObj['TaskId'] = 'ABC123'
	taskObj['routingKey'] = 'GREYUNI.GREYTEST'
	taskObj[GC_Utility.GC_TASKREF] = 'Ref123'
	#taskObj[GC_Utility.GC_MODULEID] = 'debug'
	#taskObj[GC_Utility.GC_CMD_DATA] = {}
	#instance.logging_callback('ch', 'method', 'properties', json.dumps(taskObj))

	#taskObj[GC_Utility.GC_MODULEID] = 'execute'
	
	#command['cmdline'] = 'ls -al'
	#command['timer'] = 10

	message = """
	This is an e-mail message to be sent in HTML format

	<b>This is HTML message.</b>
	<h1>This is headline.</h1>
	"""
	taskObj[GC_Utility.GC_MODULEID] = 'email'
	command['cmd'] = 'sendemail'
	command['msg'] = message
	command['sender'] = 'gray_lead@hq.bluenet'
	command['receivers'] = ['gray_lead@hq.bluenet']
	
	# taskObj[GC_Utility.GC_MODULEID] = 'download'
	#command['url'] = 'http://the.earth.li/~sgtatham/putty/latest/x86/putty.exe'
	# command['saveas'] = '.\\7z938-extra.7z'


	taskObj[GC_Utility.GC_CMD_DATA] = command

	# instance.logging_callback('ch', 'method', 'properties', json.dumps(taskObj))
	# taskObj[GC_Utility.GC_TASKREF] = 'Ref456'
	# taskObj[GC_Utility.GC_CMD_DATA]['url'] = 'http://bitcoin.org/bitcoin.pdf'

	instance.logging_callback('ch', 'method', 'properties', json.dumps(taskObj))
	
#	loop = 1
#	for url in urls:
#		taskObj[GC_Utility.GC_TASKREF] = 'Ref789_%d' % loop
#		loop = loop + 1
#		taskObj[GC_Utility.GC_CMD_DATA]['url'] = url
#		instance.logging_callback('ch', 'method', 'properties', json.dumps(taskObj))

	# taskObj[GC_Utility.GC_MODULEID] = 'download'
	# taskObj[GC_Utility.GC_CMD_DATA]['url'] = 'http://www.cnn.com'
	# command['saveas'] = '.\\cnn_index.html'
	# instance.logging_callback('ch', 'method', 'properties', json.dumps(taskObj))

	# taskObj[GC_Utility.GC_MODULEID] = 'download'
	# taskObj[GC_Utility.GC_CMD_DATA]['url'] = 'http://www.sightspecific.com/~mosh/www_faq/ext.html'
	# command['saveas'] = '.\\sight_specific_index.html'
	# instance.logging_callback('ch', 'method', 'properties', json.dumps(taskObj))

	time.sleep(30)
	instance.quit()
except Exception as e:
	print e
	traceback.print_exc(file=sys.stdout)
