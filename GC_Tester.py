from GCClient import GCClient
import GC_Utility
import json
import time

instance = GCClient(debug = True, enable_comms = True)

taskObj = {}
command = {}

taskObj['TaskId'] = 'ABC123'
taskObj['routingKey'] = 'GREYUNI.GREYTEST'
taskObj[GC_Utility.GC_TASKREF] = 'Ref123'

taskObj[GC_Utility.GC_MODULEID] = 'selenium'
command['cmd'] = 'execute_url'
command['url'] = 'https://www.cnn.com'
command['timer'] = 10

message = """From: CDX Test <CDXTest779@gmail.com>
To: To Person <jim@elliott-family.net>
MIME-Version: 1.0
Content-type: text/html
Subject: SMTP HTML e-mail test

This is an e-mail message to be sent in HTML format

<b>This is HTML message.</b>
<h1>This is headline.</h1>
"""
# taskObj[GC_Utility.GC_MODULEID] = 'email'
# command['cmd'] = 'sendemail'
# command['msg'] = message
# command['sender'] = 'CDXTest779@gmail.com'
# command['receivers'] = 'jim@elliott-family.net'

# taskObj[GC_Utility.GC_MODULEID] = 'download'
# command['url'] = 'http://the.earth.li/~sgtatham/putty/latest/x86/putty.exe'
# command['saveas'] = '.\\7z938-extra.7z'


taskObj[GC_Utility.GC_CMD_DATA] = command

instance.logging_callback('ch', 'method', 'properties', json.dumps(taskObj))
taskObj[GC_Utility.GC_TASKREF] = 'Ref456'
taskObj[GC_Utility.GC_CMD_DATA]['url'] = 'https://bitcoin.org/bitcoin.pdf'

instance.logging_callback('ch', 'method', 'properties', json.dumps(taskObj))

# taskObj[GC_Utility.GC_TASKREF] = 'Ref789'
# taskObj[GC_Utility.GC_CMD_DATA]['url'] = 'http://127.0.0.1'
# instance.logging_callback('ch', 'method', 'properties', json.dumps(taskObj))

taskObj[GC_Utility.GC_MODULEID] = 'download'
taskObj[GC_Utility.GC_CMD_DATA]['url'] = 'https://www.cnn.com'
command['saveas'] = '.\\cnn_index.html'
instance.logging_callback('ch', 'method', 'properties', json.dumps(taskObj))

taskObj[GC_Utility.GC_MODULEID] = 'download'
taskObj[GC_Utility.GC_CMD_DATA]['url'] = 'https://bitcoin.org/bitcoin.pdf'
command['saveas'] = '.\\bitcoin.pdf'
instance.logging_callback('ch', 'method', 'properties', json.dumps(taskObj))

time.sleep(5*60)
instance.quit()