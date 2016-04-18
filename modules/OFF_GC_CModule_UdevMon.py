"""
File: GC_CModule_UdevMon.py
Description:
	This is a Udev monitor specific for USB Devices. However, this uses the pyudev library to handle filtering and other udev interactions.
ModuleID: udevmon
Command Structure:
	<TODO>
	filter: String - change the filter used againt the docker event feed.
	filter_action: String - add, replace, delete, delete_all for the filters.

Response Structure:
	<TODO>
"""
from GC_CModule import GC_CModule
import GC_Utility

# from contextlib import closing
# from socket import socket, AF_UNIX
# from subprocess import Popen, PIPE
# from sys import version_info

from pyudev import Context, Monitor, MonitorObserver

# from threading import Thread
import json
import queue
import pprint
import logging

# Setup Logging:
LoggerName = 'gcclient.module.'+__name__
logger = logging.getLogger(LoggerName)
logger.setLevel(logging.DEBUG)


class GC_CModule_UdevMon(GC_CModule):
	MODULE_ID = 'udevmon'

	def __init__(self, gcclient):
		self.gcclient = gcclient
		logger.debug('Initialize Module: %s', self.MODULE_ID)

		# Running State
		self.Running = True

		# Setup pyudev contect and monitor:
		# 1 - Ensure the udev context and monitor is setup:
		self.setupUdevMonitor()
		# 2 - Get and send the current device list:
		gccommand = {}
		gccommand[GC_Utility.GC_MODULEID] = self.MODULE_ID
		response = self.getCurrentUSBDevices()
		logger.debug('Sending udev init data...')
		self.gcclient.sendResult(gccommand, response);
		# 3 - Start the Udev Monitor:
		self.startUdevMonitor(callback=self.udevMonitorHandler)

	def setupUdevMonitor(self, filter_subsystem='usb'):
		logger.debug('Setting up udev context...')
		self.udev_context = Context()
		logger.debug('Setting up monitor context...')
		self.udev_monitor = Monitor.from_netlink(self.udev_context)
		logger.debug('Setting up monitor filter...')
		self.udev_monitor.filter_by(subsystem=filter_subsystem)

	def startUdevMonitor(self, callback):
		observer_name = self.MODULE_ID + '-observer'
		logger.debug('Setting up udev monitor: %s' % observer_name)
		self.udev_observer = MonitorObserver(self.udev_monitor, callback=callback, name=observer_name)
		self.udev_observer.start()

	def udevMonitorHandler(self, device):
		"""
		Watch udev event and handle each of them.
		"""
		self.parseDeviceObj(device)

	def parseDeviceObj(self, device):
		#logger.debug('Udev Device :: PCI Slot Name: %s' % pprint.pformat(device.find_parent('pci')['PCI_SLOT_NAME']))
		new_device_obj = {}
		# Get the device converted to a standard dict: (better for JSON sending)
		for item in device.items():
			new_device_obj[item[0]]=item[1]

		# Get the tags, if they are there:
		tags_from_device = list(device.tags)
		if len(tags_from_device) > 0:
			new_device_obj['TAGS'] = tags_from_device
		else:
			new_device_obj['TAGS'] = []

		#logger.debug('Udev Device Dict:\n%s' % pprint.pformat(new_device_obj))
		return new_device_obj

	def getCurrentUSBDevices(self, filter_subsystem='usb'):
		logger.debug('Getting current USB Devices...')
		finalObj = {}
		parsed_devices = []

		# Parse all USB Devices:
		for device in self.udev_context.list_devices(subsystem=filter_subsystem):
			new_device_obj = self.parseDeviceObj(device)
			parsed_devices.append(new_device_obj)

		# Prep for output:
		finalObj['current_devices'] = parsed_devices
		#logger.debug('Udev Devices Dict:\n%s' % pprint.pformat(finalObj))

		return finalObj
		# jEnc = json.JSONEncoder(skipkeys=True)
		# json_blob = jEnc.encode(finalObj)
		# logger.debug('Udev Devices JSON:\n%s' % pprint.pformat(json_blob))

	"""
	Function: handleTask
	Description: handle download commands
	"""
	def handleTask(self, gccommand):
		#self.gcclient.log(GC_Utility.DEBUG, 'downloadFile : Sending result...');
		logger.debug('Sending result...')
		self.gcclient.sendResult(gccommand, response);

	def getModuleId(self):
		return self.MODULE_ID

	def quit(self):
		self.Running = False
		self.udev_observer.send_stop()
		return True
