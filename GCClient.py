<<<<<<< HEAD
"""
Filename: GCClient.py
Description: main object for the GCClient. The client is divided into 3 primary sections. The Client (This file) which manages commands and response between the communications module (GCClient_Comms) and the Client Modules (GC_CModule*). The Client contains some built in commands, which manage core diagnostics and system management functionality.

The GCClient reads all configurable items from the gcclient.ini.

Each implemented GC_CModule is responsible for its own memory, file and/or process management and cleanup.

All other modules are loaded dynamically by loading any GC_CModule_*.py file that implements the GC_CModule class. The CModules are identified by ModuleId's defined by each CModule. Each command received by GCClient_Comms is handled by the logging_callback function, which will attempt to match the ModuleID embedded in the command with a ModuleID associated with either a GC_CModule or one of the built-in GCClient functions.

GCClient brokers responses and logs between running GC_CModules and the GCClient_Comms.

GCClient layout:
Section 1: Initialization functions (__init__, isRunning, readConfig, readConfigItem)
Section 2: Module handling (loadModules, reloadModules, loadModule)
Section 3: Command receipt and response functions (logging_callback, sendResult, sendOneOffResult)
Section 4: Built-in functions (quit, set_debug, generate_diagnostics)
"""
import GCClient_Comms
import GC_CModule
import configparser
import socket
import os
import sys
import platform
import json
import hashlib
from datetime import datetime
from datetime import timedelta
import GC_Utility
import threading
import imp
import inspect
import subprocess
import inspect
import traceback, sys
import logging
import pprint
import copy

# Setup Logging:
LoggerName = 'gcclient.'+__name__
logger = logging.getLogger(LoggerName)

GC_VERSION = '2016_v5.1'

GC_CONFIG_FILENAME = 'gcclient.ini'
GC_CONFIG_CATEGORY = 'DEFAULT'
GC_MODULE_DIR = './modules/'

# Standard config items
GC_AMQP_HOST = 'AMQP_HOST'
GC_AMQP_PORT = 'AMQP_PORT'
GC_USERID = 'USERID'
GC_PASSWORD = 'PASSWORD'
GC_RESP_EXCHANGE = 'RESP_EXCHANGE'
GC_RESP_KEY = 'RESP_KEY'
GC_LOG_EXCHANGE = 'LOG_EXCHANGE'
GC_LOG_KEY = 'LOG_KEY'
GC_TASK_EXCHANGE = 'TASK_EXCHANGE'
GC_TASK_KEY = 'TASK_KEY'
GC_SCHOOLNAME = 'SCHOOLNAME'
GC_CLIENTID = 'CLIENTID'

# Config items for AQMP SSL Certs
GC_COMMS_AQMP_CERTFILE = 'AQMP_CERTFILE'
GC_COMMS_AQMP_KEYFILE  = 'AQMP_KEYFILE'
GC_COMMS_AQMP_CAFILE   = 'AQMP_CAFILE'

GC_ALL_TASKS = 'all.tasks'
GC_TASK_ROUTINGKEY = '.tasks'

class GCClient(object):
    gc_modules = {}
    gc_threads = []

    """
    Function: __init__
    Description: Initialize the GCClient, GCClient_Comms and GC_CModules.
    1. Initialize class variables
    2. Read config file
    3. Initialize GCClient_Comms
    4. Initialize GC_CModules

    """
    def __init__(self, debug = False, version=GC_VERSION, enable_comms = True, config_file=GC_CONFIG_FILENAME, client_id=None, gc_amqp_host=None, gc_amqp_port=5672, gc_amqp_sslon=False):

        # Initialize class management variables.
        self.Running = True
        self.numTasks = 0

        if (debug):
            #logger.setLevel(logging.DEBUG)
            self.logging_level = GC_Utility.DEBUG
        else:
            #logger.setLevel(logging.INFO)
            self.logging_level = GC_Utility.INFO

        logger.info('Initializing GCClient core...')
        logger.debug('Init Vars :: debug: %s', debug)
        logger.debug('Init Vars :: version: %s', version)
        logger.debug('Init Vars :: enable_comms: %s', enable_comms)
        logger.debug('Init Vars :: config_file: %s', config_file)
        logger.debug('Init Vars :: client_id: %s', client_id)
        logger.debug('Init Vars :: gc_amqp_host: %s', gc_amqp_host)
        logger.debug('Init Vars :: gc_amqp_port: %s', gc_amqp_port)
        logger.debug('Init Vars :: gc_amqp_sslon: %s', gc_amqp_sslon)

        # Set global version:
        self.version = version

        # Set client id, if specified
        self.clientid = client_id

        # Read Configuration:
        self.readConfig(config_file=config_file)

        # Run the initial diagnostics:
        self.generate_diagnostics()

        self.ENABLE_COMMS = enable_comms
        if self.ENABLE_COMMS:

            cur_amqp_host = self.gc_host
            if gc_amqp_host is not None:
                cur_amqp_host = gc_amqp_host

            # Setup Routing Keys:
            routing_keys = []
            routing_keys.append(str(GC_ALL_TASKS))
            routing_keys.append(str(self.school_name) + str(GC_TASK_ROUTINGKEY))
            routing_keys.append(str(self.uuid) + str(GC_TASK_ROUTINGKEY))
            logger.debug("routing_keys: %s" % routing_keys)

            # Initialize Comms Module
            self.comms = GCClient_Comms.GCClient_Comms(gc_host = cur_amqp_host,
                                                       gc_port = self.gc_port,
                                                       userid = self.userid,
                                                       password = self.password,
                                                       certfile=self.aqmp_certfile,
                                                       keyfile=self.aqmp_keyfile,
                                                       cafile=self.aqmp_cafile,
                                                       resp_exchange=self.resp_exchange,
                                                       mon_exchange=self.task_exchange,
                                                       mon_routing_key=routing_keys,
                                                       mon_callback=self.logging_callback)

            # Start Listening to exchanges
            # t = threading.Thread(name=GC_ALL_TASKS,
            #                      target=self.comms.monitor,
            #                      args=(self.task_exchange, [GC_ALL_TASKS, self.school_name + GC_TASK_ROUTINGKEY,  self.uuid + GC_TASK_ROUTINGKEY], self.logging_callback))

            # Start Listening to exchanges
            # t = threading.Thread(name=GC_ALL_TASKS,
            #                      target=self.comms.monitor,
            #                      args=(self.task_exchange, routing_keys, self.logging_callback))
            # t.start()
            # self.gc_threads.append(t)

            t = threading.Thread(name=GC_ALL_TASKS,
                                 target=self.comms.initiate_connection)
            t.start()
            self.gc_threads.append(t)
        # Load all CModules and built-in functions
        self.loadModules()

    """
    Function: isRunning
    Description: returns the running state of the GCClient
    """
    def isRunning(self):
        return self.Running

    """
    Function: readConfig
    Description: Reads all the default config items. If GC_CLIENTID isn't defined, use the hostname
    """
    def readConfig(self, config_file=GC_CONFIG_FILENAME):
        logger.info('START :: Config being processed...')
        logger.debug('Config file to be processed: %s', config_file)
        config = configparser.ConfigParser()
        config_file = open(config_file)
        config.readfp(config_file)
        config_file.close()

        # Base AMQP Config
        self.gc_host = config.get(GC_CONFIG_CATEGORY, GC_AMQP_HOST)
        logger.debug('gc_host: %s', self.gc_host)
        self.gc_port = config.get(GC_CONFIG_CATEGORY, GC_AMQP_PORT)
        logger.debug('gc_port: %s', self.gc_port)
        self.userid = config.get(GC_CONFIG_CATEGORY, GC_USERID)
        logger.debug('userid: %s', self.userid)
        self.password = config.get(GC_CONFIG_CATEGORY, GC_PASSWORD)
        logger.debug('password: %s', self.password)

        # SSL AMQP Support
        self.aqmp_cafile = config.get(GC_CONFIG_CATEGORY, GC_COMMS_AQMP_CAFILE)
        logger.debug('aqmp_cafile: %s', self.aqmp_cafile)
        self.aqmp_certfile = config.get(GC_CONFIG_CATEGORY, GC_COMMS_AQMP_CERTFILE)
        logger.debug('aqmp_certfile: %s', self.aqmp_certfile)
        self.aqmp_keyfile = config.get(GC_CONFIG_CATEGORY, GC_COMMS_AQMP_KEYFILE)
        logger.debug('aqmp_keyfile: %s', self.aqmp_keyfile)

        # Tasking AMQP Config
        self.task_exchange = config.get(GC_CONFIG_CATEGORY, GC_TASK_EXCHANGE)
        logger.debug('task_exchange: %s', self.task_exchange)
        self.task_key = config.get(GC_CONFIG_CATEGORY, GC_TASK_KEY)
        logger.debug('task_key: %s', self.task_key)

        # Results AMQP Config
        self.resp_exchange = config.get(GC_CONFIG_CATEGORY, GC_RESP_EXCHANGE)
        logger.debug('resp_exchange: %s', self.resp_exchange)
        self.resp_key = config.get(GC_CONFIG_CATEGORY, GC_RESP_KEY)
        logger.debug('resp_key: %s', self.resp_key)

        # Logging AMQP Config
        self.log_exchange = config.get(GC_CONFIG_CATEGORY, GC_LOG_EXCHANGE)
        logger.debug('log_exchange: %s', self.log_exchange)
        self.log_key = config.get(GC_CONFIG_CATEGORY, GC_LOG_KEY)
        logger.debug('log_key: %s', self.log_key)

        # Set School Info:
        if config.has_option(GC_CONFIG_CATEGORY, GC_SCHOOLNAME):
            self.school_name = config.get(GC_CONFIG_CATEGORY, GC_SCHOOLNAME)
        else:
            self.school_name = None
        logger.info('school_name: %s', self.school_name)

        # Set Client:
        #If GC_CLIENTID isn't defined, use the hostname
        if self.clientid == None:
            if (config.has_option(GC_CONFIG_CATEGORY, GC_CLIENTID)):
                self.clientid = config.get(GC_CONFIG_CATEGORY, GC_CLIENTID)
            else:
                self.clientid = socket.gethostname()
        logger.info('clientid: %s', self.clientid)

        # Set UUID:
        if self.school_name == None:
            self.uuid = self.clientid
        else:
            self.uuid = self.school_name + "_" + self.clientid
        logger.info('uuid: %s', self.uuid)

        logger.info('END :: Config processing complete...')

    """
    Function: readConfigItem
    Description: Reads a specific config item from the config file. This is function enables GC_CModules to access config file items
    """
    def readConfigItem(self, configItem):
        config = configparser.ConfigParser()
        config_file = open(GC_CONFIG_FILENAME)
        config.readfp(config_file)
        c_item = config.get(GC_CONFIG_CATEGORY, configItem)
        config_file.close()
        
        return c_item

    """
    Function: loadModules
    Description: Loads built-in and dynamic GC_CModules. Stores all modules into the self.gc_modules dictionary, referenced by their ModuleID
    1. Load built-in functions, loggingCallback will check for methods vs. GC_CModule objects
    2. Parse the current directory for all GC_CModule_*.py files
    """
    def loadModules(self):
        # Add built in functions to the gc_modules dictionary`
        self.gc_modules[GC_Utility.GC_MOD_DIAG] = self.generate_diagnostics
        self.gc_modules[GC_Utility.GC_MOD_QUIT] = self.quit
        self.gc_modules[GC_Utility.GC_MOD_DEBUG] = self.setDebug
        self.gc_modules[GC_Utility.GC_MOD_RELOAD] = self.reloadModules
        logger.debug('built-in modules: %s', self.gc_modules.keys())

        # Walk the current directory and load any file GC_CModule_*.py
        for file in os.listdir(GC_MODULE_DIR):
            file = GC_MODULE_DIR + file
            (path, name) = os.path.split(file)
            (name, ext) = os.path.splitext(name)

            # Check that this is a file with a name GC_CModule_*.py
            if os.path.isfile(file) and name.startswith('GC_CModule_') and ext == '.py':
                logger.debug('Module File Found: %s', file)
                # Load the module
                self.loadModule(file)

    """
    Function: reloadModules
    Description: Reloads all modules by quiting all modules (to force them to clean-up) and re-runs loadModules
    """
    def reloadModules(self):
        # Shutting down modules
        for name in self.gc_modules:
            m = self.gc_modules[name]
            if not inspect.ismethod(m):
                #self.log(GC_Utility.INFO, "Shutting down " + m.getModuleId())
                logger.info('Shutting down ' + m.getModuleId())
                m.quit()
                del m

        self.loadModules()

    """
    Function: loadModule
    Description: Loads an individual module from a file.
    1. Check for the correct filename
    2. dynamically load the module
    3. verify that the module is a GC_CModule
    4. initialize the GC_CModule
    5. add the GC_CModule to the self.gc_modules dictionary, referenced by the ModuleID reported by the GC_CModule
    """
    def loadModule(self, filename):
        (path, name) = os.path.split(filename)
        (name, ext) = os.path.splitext(name)

        # Check that this is a file exists
        if os.path.isfile(filename) and ext == '.py':

            # Load the module
            (f, filename, data) = imp.find_module(name, [path])
            module = imp.load_module(name, f, filename, data)

            # Check module for a GC_CModule class
            for name in dir(module):
                obj = getattr(module, name)

                # Check module for a GC_CModule subclass, and not GC_CModule
                if name != 'GC_CModule' and inspect.isclass(obj) and issubclass(obj, GC_CModule.GC_CModule):
                    # Load the module, and add it to the gc_modules dictionary
                    try:
                        logger.debug('Loading GC_CModule: ' + obj.__name__)
                        m = obj(self)
                        self.gc_modules[m.getModuleId()] = m
                        
                        logger.info('Loaded Module: ' + m.getModuleId())
                    except AssertionError:
                        logger.warn('Failed to load module ' + name, exc_info=True)
    """
    Function: reloadModule
    Description: TODO reload an individual module without reloading all of them. This is tricky since one needs to ID the file to reload from.
    """
    # def reloadModule(self, moduleid):
        # m = self.gc_modules[moduleid]

        # if not inspect.ismethod(m):
            # mod_class = m.__class__
            # cname = m.__name__
            # m.quit()
            # reload(cname)

    """
    Function: logging_callback
    Description: Callback from the GCClient_Comms.
    Expected json fields:
        TaskCreateDT: String (YYYYMMDDTHHMMSS.SSS) <withheld>
        ModuleID: Integer Associated with command module
        TaskRef: Integer defined by module
        CommandData: Key Value array, defined by module

    When a message is received:
    1. the json blob is decoded
    2. initial headers are read
    3. receive time is set
    4. determine the command or module being requested.
    5. check self.gc_modules for a matching function/module (send an error response if not found)
    6. pass the task object to the function/module
    """
    def logging_callback(self, ch, method, properties, body):
    #@defer.inlineCallbacks
    #def logging_callback(self, queue_object):
        #logger.debug(queue_object)
        #ch,method,properties,body = yield queue_object.get()

        # Show Raw Body:
        logger.debug("Raw body: %r" % body)

        # Decode the message as json
        rcvd_task = json.loads(body.decode("utf-8"))
        logger.debug("Raw task: %s", rcvd_task)

        # Set some fields used in the response (uuid, receieve time, etc)
        rcvd_task[GC_Utility.GC_CLIENTID] = self.uuid
        rcvd_task[GC_Utility.GC_RECEIVE_TIME] = GC_Utility.currentZuluDT()
        logger.debug("GC_CLIENTID: %s", rcvd_task[GC_Utility.GC_CLIENTID])
        logger.debug("GC_RECEIVE_TIME: %s", rcvd_task[GC_Utility.GC_RECEIVE_TIME])

        logger.info("Received task %s at %s", rcvd_task[GC_Utility.GC_TASKREF], rcvd_task[GC_Utility.GC_RECEIVE_TIME])

        # This isn't used yet... someday...
        # TODO: Use the create time from the received task.
        create_time = datetime.utcnow() #dateutil.parser.parse(rcvd_task[GC_Utility.GC_RECEIVE_TIME])
        logger.debug("create_time: %s", create_time)

        # Figure out which module... key/value pair on moduleid with objects....
        if rcvd_task[GC_Utility.GC_MODULEID] in self.gc_modules:
            # Check create time + 5min, throw it away if it's too old
            # TODO: use create time!!
            if (datetime.utcnow() - create_time)  < timedelta(seconds=(60*5)):
                try:
                    # If the ModuleID matches a built-in function, create a response object, call the function and store the results
                    # else pass the task to the matched GC_CModule
                    if (inspect.ismethod(self.gc_modules[rcvd_task[GC_Utility.GC_MODULEID]])):
                        response = {}
                        response['startTime'] = GC_Utility.currentZuluDT()
                        response['result'] = self.gc_modules[rcvd_task[GC_Utility.GC_MODULEID]]()
                        self.sendResult(rcvd_task, response)
                    else:
                        self.gc_modules[rcvd_task[GC_Utility.GC_MODULEID]].handleTask(rcvd_task)
                except Exception as e:
                    logger.warn("GCClient.logging_callback caught exception", exc_info=True)
                    #traceback.print_exc(file=sys.stdout)
            # Task was too old
            else:
                logger.info(rcvd_task[GC_Utility.GC_TASK_ID] + " create time > 5 min old ")
        # Module ID no found
        else:
            logger.warn(rcvd_task[GC_Utility.GC_MODULEID] + " not found in ", exc_info=True)

        # TODO: Automatic diagnostics or logging every 100 tasks
        if (self.numTasks % 100):
            logger.debug("At some point this will send memory info.")

    """
    Function: sendResult
    Description: handle sending response objects back to the server.
    """
    def sendResult(self, taskObj, respData):
        # Set assemble the task and response objects.
        taskObj[GC_Utility.GC_COMPLETE_TIME] = GC_Utility.currentZuluDT()
        taskObj[GC_Utility.GC_RESP_DATA] = respData

        # delete unnecessary command data before returning the results
        if GC_Utility.GC_CMD_DATA in taskObj:
            del taskObj[GC_Utility.GC_CMD_DATA]

        # Print and/or send the compiled response
        logger.debug("Printing TaskObj: %r" % pprint.pformat(json.dumps(taskObj)))

        if self.ENABLE_COMMS:
            self.comms.publish(routing_key=self.resp_key, message = json.dumps(taskObj))


    def sendOneOffResult(self, moduleId, respData):
        # 2. ModuleID: Integer Associated with command module<br>
        # 3. TaskRef: Integer defined by module<br>
        # 4. RecieveTime: String (YYYYMMDDZHHMMSS.SSS) <br>
        # 5. CompleteTime: String (YYYYMMDDZHHMMSS.SSS) <br>
        # 6. ResponseData: Key Value array, defined by module<br>
        taskObj = {}
        taskObj[GC_Utility.GC_MODULEID] = moduleId
        taskObj[GC_Utility.GC_COMPLETE_TIME] = GC_Utility.currentZuluDT()
        taskObj[GC_Utility.GC_RESP_DATA] = respData

        logger.debug("Printing TaskObj: %r" % pprint.pformat(json.dumps(taskObj)))

        if self.ENABLE_COMMS:
            self.comms.publish(routing_key=self.resp_key, message = json.dumps(taskObj))


    def log(self, log_level, msg):
        if (log_level < self.logging_level):
            return;

        log_msg = {}
        log_msg[GC_Utility.GC_LOG_DATETIME] = GC_Utility.currentZuluDT()
        log_msg[GC_Utility.GC_CLIENTID] = self.uuid
        log_msg[GC_Utility.GC_LOG_MSG] = msg

        curframe = inspect.currentframe()
        calframe = inspect.getouterframes(curframe, 2)

        log_msg['caller'] = "%s:%s:%s" % (calframe[1][1], calframe[1][3], calframe[1][2])

        if (log_level == GC_Utility.DEBUG):
            log_msg['level'] = "DEBUG"
        elif (log_level == GC_Utility.WARN):
            log_msg['level'] = "WARNING"
        else:
            log_msg['level'] = "INFO"

        if self.ENABLE_COMMS:
            self.comms.publish(exchange_name = self.log_exchange, routing_key=self.log_key, type='direct', message = json.dumps(log_msg))
        else:
            logger.info(log_msg)
            #print log_msg

    def setDebug(self):
        result = ""

        if self.logging_level == GC_Utility.DEBUG:
            self.logging_level = GC_Utility.INFO
            result = "Set log level to INFO"
        else:
            self.logging_level = GC_Utility.DEBUG
            result = "Set log level to DEBUG"

        return result

    def generate_diagnostics(self):
        diag_msg = {}
        diag_msg['GC_Version'] = self.version
        diag_msg['OS'] = platform.platform() + " / " + platform.machine() + " - " + platform.processor() + " :: " + platform.system()
        diag_msg['PythonVer'] = platform.python_version()
        diag_msg['uname'] = platform.uname()

        # Log the diagnostics:
        logger.debug('GC_Version: %s', diag_msg['GC_Version'])
        logger.debug('OS: %s', diag_msg['OS'])
        logger.debug('PythonVer: %s', diag_msg['PythonVer'])
        logger.debug('uname: %s', diag_msg['uname'])

        file_list = {}
        for file in os.listdir("."):
            if os.path.isfile(file):
                hashme = open(file, 'rb')
                file_list[file] = hashlib.md5(hashme.read()).hexdigest()
                hashme.close()
                logger.debug('file: %s [%s]', file, file_list[file])

        diag_msg['Files'] = file_list
        try:
            if (platform.system() == 'Windows'):
                diag_msg['processList'] = subprocess.check_output('tasklist')
            elif platform.system() == 'Linux' or platform.system() == 'Darwin':
                diag_msg['processList'] = subprocess.check_output(['ps','-l'])
            else:
                diag_msg['processList'] = "Error retrieving process list on platform %s" % platform.system()
        except:
             logger.warn('Caught exception generating task list')
             diag_msg['processList'] = "Caught exception generating task list"
             
        if isinstance(diag_msg['processList'], bytes):
            diag_msg['processList'] = diag_msg['processList'].decode('utf-8')

        logger.debug('processList: %s', diag_msg['processList'])
        logger.info('Full Diag Output: %s', diag_msg)
        return diag_msg

    """
    Function: quit
    Description: Shutsdown the GCClient by calling quit on each GC_CModule and calling quit on the GCClient_Comms reference. This should make all components to shutdown any running threads and clean up anything that needs it.
    """
    def quit(self) :
        # Shutting down modules
        for name in self.gc_modules:
            m = self.gc_modules[name]
            if not inspect.ismethod(m):
                logger.info('Shutting down ' + m.getModuleId())
                try:
                   m.quit()
                except:
                   logger.debug('Caught Exception while quitting ' + m.getModuleId())
                
                del m

        # Turn off AMQP
        if self.ENABLE_COMMS:
            self.comms.quit()

        self.Running = False
        return "Quitting"
=======
"""
Filename: GCClient.py
Description: main object for the GCClient. The client is divided into 3 primary sections. The Client (This file) which manages commands and response between the communications module (GCClient_Comms) and the Client Modules (GC_CModule*). The Client contains some built in commands, which manage core diagnostics and system management functionality. 

The GCClient reads all configurable items from the gcclient.ini.

Each implemented GC_CModule is responsible for its own memory, file and/or process management and cleanup.

All other modules are loaded dynamically by loading any GC_CModule_*.py file that implements the GC_CModule class. The CModules are identified by ModuleId's defined by each CModule. Each command received by GCClient_Comms is handled by the logging_callback function, which will attempt to match the ModuleID embedded in the command with a ModuleID associated with either a GC_CModule or one of the built-in GCClient functions.

GCClient brokers responses and logs between running GC_CModules and the GCClient_Comms.

GCClient layout:
Section 1: Initialization functions (__init__, isRunning, readConfig, readConfigItem)
Section 2: Module handling (loadModules, reloadModules, loadModule)
Section 3: Command receipt and response functions (logging_callback, sendResult, sendOneOffResult)
Section 4: Built-in functions (quit, set_debug, generate_diagnostics)
"""
import GCClient_Comms
import GC_CModule
import configparser
import socket
import os
import sys
import platform
import json
import hashlib
from datetime import datetime
from datetime import timedelta
import GC_Utility
import threading
import imp
import inspect
import subprocess
import inspect
import traceback, sys
import logging

# Setup Logging:
LoggerName = 'gcclient.'+__name__
logger = logging.getLogger(LoggerName)

GC_VERSION = ''

GC_CONFIG_FILENAME = 'gcclient.ini'
GC_CONFIG_CATEGORY = 'DEFAULT'

# Standard config items
GC_AMQP_HOST = 'AMQP_HOST'
GC_AMQP_PORT = 'AMQP_PORT'
GC_USERID = 'USERID'
GC_PASSWORD = 'PASSWORD'
GC_RESP_EXCHANGE = 'RESP_EXCHANGE'
GC_RESP_KEY = 'RESP_KEY'
GC_LOG_EXCHANGE = 'LOG_EXCHANGE'
GC_LOG_KEY = 'LOG_KEY'
GC_TASK_EXCHANGE = 'TASK_EXCHANGE'
GC_TASK_KEY = 'TASK_KEY'
GC_SCHOOLNAME = 'SCHOOLNAME'
GC_CLIENTID = 'CLIENTID'

# Config items for AQMP SSL Certs
GC_COMMS_AQMP_CERTFILE = 'AQMP_CERTFILE'
GC_COMMS_AQMP_KEYFILE  = 'AQMP_KEYFILE'
GC_COMMS_AQMP_CAFILE   = 'AQMP_CAFILE'

GC_ALL_TASKS = 'all.tasks'
GC_TASK_ROUTINGKEY = '.tasks'

class GCClient(object):
	gc_modules = {}
	gc_threads = []
	
	"""
	Function: __init__
	Description: Initialize the GCClient, GCClient_Comms and GC_CModules.
	1. Initialize class variables
	2. Read config file
	3. Initialize GCClient_Comms
	4. Initialize GC_CModules
	
	"""
	def __init__(self, debug = False, version=GC_VERSION, enable_comms = True, config_file=GC_CONFIG_FILENAME, client_id=None, gc_amqp_host=None, gc_amqp_port=5672, gc_amqp_sslon=False):

		# Initialize class management variables.
		self.Running = True
		self.numTasks = 0

		if (debug):
			#logger.setLevel(logging.DEBUG)
			self.logging_level = GC_Utility.DEBUG
		else:
			#logger.setLevel(logging.INFO)
			self.logging_level = GC_Utility.INFO
		
		logger.info('Initializing GCClient core...')
		logger.debug('Init Vars :: debug: %s', debug)
		logger.debug('Init Vars :: version: %s', version)
		logger.debug('Init Vars :: enable_comms: %s', enable_comms)
		logger.debug('Init Vars :: config_file: %s', config_file)
		logger.debug('Init Vars :: client_id: %s', client_id)
		logger.debug('Init Vars :: gc_amqp_host: %s', gc_amqp_host)
		logger.debug('Init Vars :: gc_amqp_port: %s', gc_amqp_port)
		logger.debug('Init Vars :: gc_amqp_sslon: %s', gc_amqp_sslon)

		# Set global version:
		self.version = version

		# Set client id, if specified
		self.clientid = client_id

		# Read Configuration:
		self.readConfig(config_file=config_file)
		
		# Run the initial diagnostics:
		self.generate_diagnostics()

		self.ENABLE_COMMS = enable_comms
		if self.ENABLE_COMMS:

			cur_amqp_host = self.gc_host
			if gc_amqp_host is not None:
				cur_amqp_host = gc_amqp_host

			# Initialize Comms Module
			self.comms = GCClient_Comms.GCClient_Comms(gc_host = cur_amqp_host,
													   gc_port = self.gc_port,
													   userid = self.userid,
													   password = self.password,
													   certfile=self.aqmp_certfile,
													   keyfile=self.aqmp_keyfile,
													   cafile=self.aqmp_cafile)

			routing_keys = []
			routing_keys.append(str(GC_ALL_TASKS))
			routing_keys.append(str(self.school_name) + str(GC_TASK_ROUTINGKEY))
			routing_keys.append(str(self.uuid) + str(GC_TASK_ROUTINGKEY))
			logger.debug("routing_keys: %s" % routing_keys)

			# Start Listening to exchanges
			# t = threading.Thread(name=GC_ALL_TASKS,
			# 					 target=self.comms.monitor,
			# 					 args=(self.task_exchange, [GC_ALL_TASKS, self.school_name + GC_TASK_ROUTINGKEY,  self.uuid + GC_TASK_ROUTINGKEY], self.logging_callback))

			# Start Listening to exchanges
			t = threading.Thread(name=GC_ALL_TASKS,
								 target=self.comms.monitor,
								 args=(self.task_exchange, routing_keys, self.logging_callback))
			t.start()
			self.gc_threads.append(t)
		
		# Load all CModules and built-in functions
		self.loadModules()
	
	"""
	Function: isRunning
	Description: returns the running state of the GCClient
	"""
	def isRunning(self):
		return self.Running
	
	"""
	Function: readConfig
	Description: Reads all the default config items. If GC_CLIENTID isn't defined, use the hostname
	"""
	def readConfig(self, config_file=GC_CONFIG_FILENAME):
		logger.info('START :: Config being processed...')
		logger.debug('Config file to be processed: %s', config_file)
		config = configparser.ConfigParser()
		config.readfp(open(config_file))
		
		# Base AMQP Config
		self.gc_host = config.get(GC_CONFIG_CATEGORY, GC_AMQP_HOST)
		logger.debug('gc_host: %s', self.gc_host)
		self.gc_port = config.get(GC_CONFIG_CATEGORY, GC_AMQP_PORT)
		logger.debug('gc_port: %s', self.gc_port)
		self.userid = config.get(GC_CONFIG_CATEGORY, GC_USERID)
		logger.debug('userid: %s', self.userid)
		self.password = config.get(GC_CONFIG_CATEGORY, GC_PASSWORD)
		logger.debug('password: %s', self.password)
		
		# SSL AMQP Support
		self.aqmp_cafile = config.get(GC_CONFIG_CATEGORY, GC_COMMS_AQMP_CAFILE)
		logger.debug('aqmp_cafile: %s', self.aqmp_cafile)
		self.aqmp_certfile = config.get(GC_CONFIG_CATEGORY, GC_COMMS_AQMP_CERTFILE)
		logger.debug('aqmp_certfile: %s', self.aqmp_certfile)
		self.aqmp_keyfile = config.get(GC_CONFIG_CATEGORY, GC_COMMS_AQMP_KEYFILE)
		logger.debug('aqmp_keyfile: %s', self.aqmp_keyfile)

		# Tasking AMQP Config
		self.task_exchange = config.get(GC_CONFIG_CATEGORY, GC_TASK_EXCHANGE)
		logger.debug('task_exchange: %s', self.task_exchange)
		self.task_key = config.get(GC_CONFIG_CATEGORY, GC_TASK_KEY)
		logger.debug('task_key: %s', self.task_key)

		# Results AMQP Config
		self.resp_exchange = config.get(GC_CONFIG_CATEGORY, GC_RESP_EXCHANGE)
		logger.debug('resp_exchange: %s', self.resp_exchange)
		self.resp_key = config.get(GC_CONFIG_CATEGORY, GC_RESP_KEY)
		logger.debug('resp_key: %s', self.resp_key)

		# Logging AMQP Config
		self.log_exchange = config.get(GC_CONFIG_CATEGORY, GC_LOG_EXCHANGE)
		logger.debug('log_exchange: %s', self.log_exchange)
		self.log_key = config.get(GC_CONFIG_CATEGORY, GC_LOG_KEY)
		logger.debug('log_key: %s', self.log_key)

		# Set School Info:
		if config.has_option(GC_CONFIG_CATEGORY, GC_SCHOOLNAME):
			self.school_name = config.get(GC_CONFIG_CATEGORY, GC_SCHOOLNAME)
		else:
			self.school_name = None
		logger.info('school_name: %s', self.school_name)

		# Set Client:
		#If GC_CLIENTID isn't defined, use the hostname
		if self.clientid == None:
			if (config.has_option(GC_CONFIG_CATEGORY, GC_CLIENTID)):
				self.clientid = config.get(GC_CONFIG_CATEGORY, GC_CLIENTID)
			else:
				self.clientid = socket.gethostname()
		logger.info('clientid: %s', self.clientid)
		
		# Set UUID:
		if self.school_name == None:
			self.uuid = self.clientid
		else:
			self.uuid = self.school_name + "_" + self.clientid
		logger.info('uuid: %s', self.uuid)

		logger.info('END :: Config processing complete...')
	
	"""
	Function: readConfigItem
	Description: Reads a specific config item from the config file. This is function enables GC_CModules to access config file items
	"""
	def readConfigItem(self, configItem):
		config = configparser.ConfigParser()
		config.readfp(open(GC_CONFIG_FILENAME))

		return config.get(GC_CONFIG_CATEGORY, configItem)
	
	"""
	Function: loadModules
	Description: Loads built-in and dynamic GC_CModules. Stores all modules into the self.gc_modules dictionary, referenced by their ModuleID
	1. Load built-in functions, loggingCallback will check for methods vs. GC_CModule objects
	2. Parse the current directory for all GC_CModule_*.py files 
	"""
	def loadModules(self):
		# Add built in functions to the gc_modules dictionary`
		self.gc_modules[GC_Utility.GC_MOD_DIAG] = self.generate_diagnostics
		self.gc_modules[GC_Utility.GC_MOD_QUIT] = self.quit
		self.gc_modules[GC_Utility.GC_MOD_DEBUG] = self.setDebug
		self.gc_modules[GC_Utility.GC_MOD_RELOAD] = self.reloadModules
		logger.debug('built-in modules: %s', self.gc_modules.keys())

		# Walk the current directory and load any file GC_CModule_*.py
		for file in os.listdir("."):
			(path, name) = os.path.split(file)
			(name, ext) = os.path.splitext(name)
			
			# Check that this is a file with a name GC_CModule_*.py
			if os.path.isfile(file) and name.startswith('GC_CModule_') and ext == '.py':
				logger.debug('Module File Found: %s', file)
				# Load the module
				self.loadModule(file)
	
	"""
	Function: reloadModules
	Description: Reloads all modules by quiting all modules (to force them to clean-up) and re-runs loadModules
	"""
	def reloadModules(self):
		# Shutting down modules
		for name in self.gc_modules:
			m = self.gc_modules[name]
			if not inspect.ismethod(m):
				#self.log(GC_Utility.INFO, "Shutting down " + m.getModuleId())
				logger.info('Shutting down ' + m.getModuleId())
				m.quit()
				del m
		
		self.loadModules()
	
	"""
	Function: loadModule
	Description: Loads an individual module from a file.
	1. Check for the correct filename
	2. dynamically load the module
	3. verify that the module is a GC_CModule
	4. initialize the GC_CModule
	5. add the GC_CModule to the self.gc_modules dictionary, referenced by the ModuleID reported by the GC_CModule
	"""
	def loadModule(self, filename):
		(path, name) = os.path.split(filename)
		(name, ext) = os.path.splitext(name)
		
		# Check that this is a file exists
		if os.path.isfile(filename) and ext == '.py':
			
			# Load the module
			(f, filename, data) = imp.find_module(name, [path])
			module = imp.load_module(name, f, filename, data)
			
			# Check module for a GC_CModule class
			for name in dir(module):
				obj = getattr(module, name)
				
				# Check module for a GC_CModule subclass, and not GC_CModule
				if name != 'GC_CModule' and inspect.isclass(obj) and issubclass(obj, GC_CModule.GC_CModule):
					# Load the module, and add it to the gc_modules dictionary
					try: 
						#self.log(GC_Utility.DEBUG, "Loading GC_CModule: " + obj.__name__)
						logger.debug('Loading GC_CModule: ' + obj.__name__)
						m = obj(self)
						self.gc_modules[m.getModuleId()] = m
						#self.log(GC_Utility.INFO, "Loaded Module: " + m.getModuleId())
						logger.info('Loaded Module: ' + m.getModuleId())
					except AssertionError:
						logger.warn('Failed to load module ' + name, exc_info=True)
						#self.log(GC_Utility.WARN, "Failed to load module %s" % (name))
	"""
	Function: reloadModule
	Description: TODO reload an individual module without reloading all of them. This is tricky since one needs to ID the file to reload from.
	"""
	# def reloadModule(self, moduleid):
		# m = self.gc_modules[moduleid]
		
		# if not inspect.ismethod(m):
			# mod_class = m.__class__
			# cname = m.__name__
			# m.quit()
			# reload(cname)

	"""
	Function: logging_callback
	Description: Callback from the GCClient_Comms. 
	Expected json fields:
		TaskCreateDT: String (YYYYMMDDTHHMMSS.SSS) <withheld>
		ModuleID: Integer Associated with command module
		TaskRef: Integer defined by module
		CommandData: Key Value array, defined by module
		
	When a message is received:
	1. the json blob is decoded
	2. initial headers are read
	3. receive time is set
	4. determine the command or module being requested.
	5. check self.gc_modules for a matching function/module (send an error response if not found)
	6. pass the task object to the function/module
	"""
	def logging_callback(self, ch, method, properties, body):
		# Decode the message as json
		rcvd_task = json.loads(body)
		logger.debug("Raw task: %s", rcvd_task)

		# Set some fields used in the response (uuid, receieve time, etc)
		rcvd_task[GC_Utility.GC_CLIENTID] = self.uuid
		rcvd_task[GC_Utility.GC_RECEIVE_TIME] = GC_Utility.currentZuluDT()
		logger.debug("GC_CLIENTID: %s", rcvd_task[GC_Utility.GC_CLIENTID])
		logger.debug("GC_RECEIVE_TIME: %s", rcvd_task[GC_Utility.GC_RECEIVE_TIME])
		
		#self.log(GC_Utility.INFO, "Received task %s at %s" % (rcvd_task[GC_Utility.GC_TASKREF], rcvd_task[GC_Utility.GC_RECEIVE_TIME]))
		logger.info("Received task %s at %s", rcvd_task[GC_Utility.GC_TASKREF], rcvd_task[GC_Utility.GC_RECEIVE_TIME])
		
		# This isn't used yet... someday...
		# TODO: Use the create time from the received task.
		create_time = datetime.utcnow() #dateutil.parser.parse(rcvd_task[GC_Utility.GC_RECEIVE_TIME])
		logger.debug("create_time: %s", create_time)

		# Figure out which module... key/value pair on moduleid with objects....
		if rcvd_task[GC_Utility.GC_MODULEID] in self.gc_modules:
			# Check create time + 5min, throw it away if it's too old
			# TODO: use create time!!
			if (datetime.utcnow() - create_time)  < timedelta(seconds=(60*5)):
				try:
					# If the ModuleID matches a built-in function, create a response object, call the function and store the results
					# else pass the task to the matched GC_CModule
					if (inspect.ismethod(self.gc_modules[rcvd_task[GC_Utility.GC_MODULEID]])):
						response = {}
						response['startTime'] = GC_Utility.currentZuluDT()
						response['result'] = self.gc_modules[rcvd_task[GC_Utility.GC_MODULEID]]()
						self.sendResult(rcvd_task, response)
					else:
						self.gc_modules[rcvd_task[GC_Utility.GC_MODULEID]].handleTask(rcvd_task)
				except Exception as e:
					#self.log(GC_Utility.WARN, "GCClient.logging_callback caught exception %s" % e)
					logger.warn("GCClient.logging_callback caught exception", exc_info=True)
					#traceback.print_exc(file=sys.stdout)
			# Task was too old	
			else:
				#self.log(GC_Utility.INFO, rcvd_task[GC_Utility.GC_TASK_ID] + " create time > 5 min old ")
				logger.info(rcvd_task[GC_Utility.GC_TASK_ID] + " create time > 5 min old ")
		# Module ID no found
		else:
			#self.log(GC_Utility.INFO, rcvd_task[GC_Utility.GC_MODULEID] + " not found in ")
			logger.warn(rcvd_task[GC_Utility.GC_MODULEID] + " not found in ", exc_info=True)
		
		# TODO: Automatic diagnostics or logging ever 100 tasks
		if (self.numTasks % 100):
			#self.log(GC_Utility.INFO, "At some point this will send memory info.")
			logger.debug("At some point this will send memory info.")

	"""
	Function: sendResult
	Description: handle sending response objects back to the server.
	"""
	def sendResult(self, taskObj, respData):
		# Set assemble the task and response objects.
		taskObj[GC_Utility.GC_COMPLETE_TIME] = GC_Utility.currentZuluDT()
		taskObj[GC_Utility.GC_RESP_DATA] = respData
		
		# delete unnecessary command data before returning the results
		del taskObj[GC_Utility.GC_CMD_DATA]
		
		# Print and/or send the compiled response
		GC_Utility.print_dict(taskObj)
		
		if self.ENABLE_COMMS:
			self.comms.publish(exchange_name = self.resp_exchange, routing_key=self.resp_key, message = json.dumps(taskObj))
	
	
	def sendOneOffResult(self, moduleId, respData):
		# 2. ModuleID: Integer Associated with command module<br>
		# 3. TaskRef: Integer defined by module<br>
		# 4. RecieveTime: String (YYYYMMDDZHHMMSS.SSS) <br>
		# 5. CompleteTime: String (YYYYMMDDZHHMMSS.SSS) <br>
		# 6. ResponseData: Key Value array, defined by module<br>
		taskObj = {}
		taskObj[GC_Utility.GC_MODULEID] = moduleId
		taskObj[GC_Utility.GC_COMPLETE_TIME] = GC_Utility.currentZuluDT()
		taskObj[GC_Utility.GC_RESP_DATA] = respData
		
		GC_Utility.print_dict(taskObj)
		
		if self.ENABLE_COMMS:
			self.comms.publish(exchange_name = self.resp_exchange, routing_key=self.resp_key, message = json.dumps(taskObj))
			
			
	
	def log(self, log_level, msg):
		if (log_level < self.logging_level):
			return;

		log_msg = {}
		log_msg[GC_Utility.GC_LOG_DATETIME] = GC_Utility.currentZuluDT()
		log_msg[GC_Utility.GC_CLIENTID] = self.uuid
		log_msg[GC_Utility.GC_LOG_MSG] = msg
		
		curframe = inspect.currentframe()
		calframe = inspect.getouterframes(curframe, 2)

		log_msg['caller'] = "%s:%s:%s" % (calframe[1][1], calframe[1][3], calframe[1][2])
		
		if (log_level == GC_Utility.DEBUG):
			log_msg['level'] = "DEBUG" 
		elif (log_level == GC_Utility.WARN):
			log_msg['level'] = "WARNING"
		else:
			log_msg['level'] = "INFO"
			
		if self.ENABLE_COMMS:
			self.comms.publish(exchange_name = self.log_exchange, routing_key=self.log_key, type='direct', message = json.dumps(log_msg))
		else:
			logger.info(log_msg)
			#print log_msg
	
	def setDebug(self):
		result = ""
		
		if self.logging_level == GC_Utility.DEBUG:
			self.logging_level = GC_Utility.INFO
			result = "Set log level to INFO"
		else:
		    self.logging_level = GC_Utility.DEBUG
		    result = "Set log level to DEBUG"
	    
		return result

	def generate_diagnostics(self):
		diag_msg = {}
		diag_msg['GC_Version'] = self.version
		diag_msg['OS'] = platform.platform() + " / " + platform.machine() + " - " + platform.processor() + " :: " + platform.system()
		diag_msg['PythonVer'] = platform.python_version()
		diag_msg['uname'] = platform.uname()

		# Log the diagnostics:
		logger.debug('GC_Version: %s', diag_msg['GC_Version'])
		logger.debug('OS: %s', diag_msg['OS'])
		logger.debug('PythonVer: %s', diag_msg['PythonVer'])
		logger.debug('uname: %s', diag_msg['uname'])

		file_list = {}
		for file in os.listdir("."):
			if os.path.isfile(file):
				file_list[file] = hashlib.md5(open(file, 'rb').read()).hexdigest()
				logger.debug('file: %s [%s]', file, file_list[file])
		
		diag_msg['Files'] = file_list
		if (platform.system() == 'Windows'):
			diag_msg['processList'] = subprocess.check_output('tasklist')
		elif platform.system() == 'Linux' or platform.system() == 'Darwin':
			diag_msg['processList'] = subprocess.check_output(['ps','-l'])
		else:
			diag_msg['processList'] = "Error retrieving process list on platform %s" % platform.system()
		
		logger.debug('processList: %s', diag_msg['processList'])
		logger.info('Full Diag Output: %s', diag_msg)
		return diag_msg

	"""
	Function: quit
	Description: Shutsdown the GCClient by calling quit on each GC_CModule and calling quit on the GCClient_Comms reference. This should make all components to shutdown any running threads and clean up anything that needs it.
	"""
	def quit(self) :
		# Shutting down modules
		for name in self.gc_modules:
			m = self.gc_modules[name]
			if not inspect.ismethod(m):
				#self.log(GC_Utility.INFO, "Shutting down " + m.getModuleId())
				logger.info('Shutting down ' + m.getModuleId())
				m.quit()
				del m
		
		# Turn off AMQP
		if self.ENABLE_COMMS:
			self.comms.quit()

		self.Running = False
		return "Quitting"

			

		
>>>>>>> origin/master
