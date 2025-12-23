#!/usr/bin/env python

import os, sys
import argparse
import subprocess
import logging
import json
import time
import platform
from datetime import datetime
from datetime import timedelta
from subprocess import Popen, PIPE


### Version 1.4.0 - 10/20/2022 - Added better Alert Logic ###
### Run 'python integralStauts.py --help' to see all options
###############################################################


### Input Argument Parsing ###
parser = argparse.ArgumentParser()
parser.add_argument("--serial", help="path of the serial device connected to integral",
					type=str, required=True)
parser.add_argument("--interrogate", help="print out all the current signal info - bypass main loop",
					action="store_true")
parser.add_argument("--rx0", help="expected output of the rx0 command",
					type=str, default="")
parser.add_argument("--rx1", help="expected output of the rx1 command",
					type=str, default="")
parser.add_argument("--tx0", help="expected output of the tx0 command",
					type=str, default="")
parser.add_argument("--tx1", help="expected output of the tx1 command",
					type=str, default="")
parser.add_argument("--input", help="expected input mode",
					type=str, choices = ['bot', 'top', 'thru', 'swap'], default="")
parser.add_argument("--fix", help="attempt to fix using hotplug if errors discovered",
					action="store_const", const=True, default=False)
parser.add_argument("--reboot", help="perform a managed shutdown if max fix attempts fail | mute file will be created and stop further reboots, until resolved",
					action="store_const", const=True, default=False)
parser.add_argument("--notify", help="notify support of bad states | mute file will be created and mute further alerts, until resolved",
					action="store_const", const=True, default=False)
parser.add_argument("--debug", help="print debug elements to the console",
					action="store_const", const=logging.DEBUG, default=logging.INFO)
parser.add_argument("--force", help="if an alert is needed, ignore the state of the mutefile and submit all alerts",
					action="store_const", const=True, default=False)					
parser.add_argument("--tries", help="number of attempts to fix an issue, before standing down",
					type=int, default=3)
parser.add_argument("--logPath", help="set a custom logging path",
					type=str)
args = parser.parse_args()


### Initialize Logging ###
"""" Logfile Logging Handler """
log = logging
mainLogger = log.getLogger()
mainLogger.setLevel(log.DEBUG)
LOGGING_PATH = args.logPath if args.logPath else "/Users/t1user/Library/Logs/integralStatus.log"
fileHandler = log.FileHandler(LOGGING_PATH)
fileHandler.setLevel(log.INFO)
fileHandler.setFormatter(log.Formatter(""))
mainLogger.addHandler(fileHandler)
log.info("-------------------------------------------------")
fileHandler.setFormatter(log.Formatter("%(asctime)s :: %(levelname)s :: %(message)s"))
mainLogger.addHandler(fileHandler)
""" Consoler Logging Handler """
consoleHandler = log.StreamHandler(sys.stdout)
consoleHandler.setLevel(args.debug)
consoleHandler.setFormatter(log.Formatter("%(message)s"))
mainLogger.addHandler(consoleHandler)
log.debug("Input Args: {}".format(args))


# Global Variables #
interpreter = sys.executable
pyVers = str(sys.version_info[0]) + str(sys.version_info[1])
compiledPath = "compiled2" if pyVers == "27" else "compiled{}".format(pyVers)
serialScriptPath = "/Local/scripts/serial/integralSerial.py"
hostname = platform.node()


## Class Initializations ##
#######################################################


class integralInterface:
	""" Class to interface with the Integral """

	def __init__(self, serial, interpreter = sys.executable, serialScriptPath = "/Local/scripts/serial/integralSerial.py"):
		self.serial = serial
		self.interpreter = interpreter
		self.serialScriptPath = serialScriptPath

	def runProcess(self, command, log = log):
		log.debug("Command: {}".format(command))
		process = Popen(command, stdout=PIPE, stderr=PIPE)
		stdout, stderr = process.communicate()
		rc = process.returncode
		stdout, stderr = stdout.rstrip(), stderr.rstrip()
		stdout, stderr = stdout.decode('utf-8'), stderr.decode('utf-8')
		log.debug("stdout: {}".format(stdout))
		log.debug("stderr: {}".format(stderr))
		return(stdout, stderr, rc)

	def compare(self, expectedOutput, integralCommand, log = log):
		command = [self.interpreter, self.serialScriptPath, self.serial, integralCommand]
		stdout, stderr, rc = self.runProcess(command)
		if stderr: # should only happen if serial port is busy?
			log.error("error executing command - {}".format(integralCommand))
			return(False, stdout, stderr)
		else:
			if expectedOutput in stdout:
				log.info("MATCH: {} == {}".format(integralCommand, stdout))
				return(True, stdout, stderr)
			else:
				log.info("MISMATCH: {} == {}".format(integralCommand, stdout))
				return(False, stdout, stderr)

	def hotplug(self, tryNum, tryMax, log = log):
		log.info("Attempting to fix with hotplug {}/{} ...".format(tryNum,tryMax))
		command = [self.interpreter, self.serialScriptPath, self.serial, "sendHotplug"]
		self.runProcess(command)
		time.sleep(15)

	def restart(self, tryNum, tryMax, log = log):
		log.info("Attempting to fix by power cycling integral {}/{} ...".format(tryNum,tryMax))
		command = [self.interpreter, self.serialScriptPath, self.serial, "reboot"]
		self.runProcess(command)
		time.sleep(30)


class integralSerialInterface(integralInterface):
	""" Class to access serial communication with Integral """

	def checkArg(self, desiredPort, log = log):
		try:
			import serial.tools.list_ports
			portObjects = list(serial.tools.list_ports.comports())
			allPorts = []
			for port in portObjects:
				allPorts.append(port[0])
			log.debug("Serial Ports Avaliable: {}".format(allPorts))
			trash, desiredPort = desiredPort.split('.')
			real = any(desiredPort in entry for entry in allPorts)
			if real == False:
				log.critical("The desired serial port is not shown in the list of avaliable serial ports")
				return False
			else:
				return True
		except Exception as e:
			log.warning('Could not verify argument is a valid serial port... Exception: {} ....Continuing...'.format(e))
			return True

	def checkComm(self, serial, log = log):
		command = [self.interpreter, self.serialScriptPath, serial, 'getVersion']
		stdout, stderr, rc = integralInterface.runProcess(self, command)
		if stderr or ("FW" not in stdout):
			log.critical("Integral is not responding to serial communication")
			return False, False
		else:
			try:
				log.debug("Parsing Firmware Info: {}".format(stdout))
				version = stdout.split("FW: ",1)[1]
				v1major, v1minor, v2major, v2minor = version.split(".")
				v1 = float(v1major + "." + v1minor)
				v2 = float(v2major + "." + v2minor)
				log.debug("Parsed Versions - {} - {}".format(v1,v2))
				if v1 >= 2.50 and v2 >= 2.50:
					return True, True
				else:
					return True, False
			except Exception as e:
				log.warning("Failed to parse Firmware Version - {}".format(e))
				return True, False


class muteFiles:
	""" Class to handle manipulation of mute files """

	def __init__(self, fileName, filePath = "/Users/t1user/Documents/integralCheck/", log = log):
		self.fileName, self.filePath = fileName, filePath
		try:
			if not os.path.exists(filePath):
				os.mkdir(self.filePath)
			f = open(self.filePath + self.fileName, "a+")
			f.close()
		except Exception as e:
			log.error("Unable to instantiate mute file: {}".format(e))

	def status(self):
		f = open(self.filePath + self.fileName, "r")
		content = f.readline()
		f.close()
		log.debug("{} Content: {}".format(self.fileName, content))
		if content == "1":
			return "MUTED"
		elif content == "0":
			return "UNMUTED"
		else:
			log.error("Mute file {} gave unexpected output - {} - defaulting to UNMUTED".format(self.fileName, content))
			return "UNMUTED"

	def mute(self):
		f = open(self.filePath + self.fileName, "w")
		f.write("1")
		f.close()

	def unMute(self):
		f = open(self.filePath + self.fileName, "w")
		f.write("0")
		f.close()



## Funcitons Initialization ##
#######################################################
 

def runProcess(command):
	log.debug("Command: {}".format(command))
	process = Popen(command, stdout=PIPE, stderr=PIPE)
	stdout, stderr = process.communicate()
	rc = process.returncode
	stdout, stderr = stdout.rstrip(), stderr.rstrip()
	stdout, stderr = stdout.decode('utf-8'), stderr.decode('utf-8')
	log.debug("stdout: {}".format(stdout))
	log.debug("stderr: {}".format(stderr))
	return(stdout, stderr, rc)


# def notify(message, mute):
# 	subject = "{} - Integral Signal Check".format(hostname)
# 	recipient = "support@t1v.com"
# 	email = [interpreter,'/Local/scripts/sendServerEmail.py','-s',subject,'-message',message,recipient]
# 	eventReport = [interpreter,'/Local/scripts/{}/ttEventReport.pyc'.format(compiledPath),'-s',subject,'-t','integral','-m',message]
# 	# Send email and TTEvent
# 	runProcess(eventReport)
# 	muteStatus = mute.status()
# 	if muteStatus == "UNMUTED" or args.force:
# 		runProcess(email)
# 		mute.mute()
# 		log.info("Alert Sent")
# 	else:
# 		log.info("Alerts Muted")


def alertEmail(message, mute):
	subject = "{} - Integral Signal Check".format(hostname)
	recipient = "support@t1v.com"
	email = [interpreter,'/Local/scripts/sendSupportAlert.py','-s',subject,'-m',message]
	muteStatus = mute.status()
	if muteStatus == "UNMUTED" or args.force:
		runProcess(email)
		mute.mute()
		log.info("Alert Sent")
	else:
		log.info("Alerts Muted")

def alertEvent(message):
	subject = "{} - Integral Signal Check".format(hostname)
	eventReport = [interpreter,'/Local/scripts/{}/ttEventReport.pyc'.format(compiledPath),'-s',subject,'-t','integral','-m',message]
	runProcess(eventReport)


def reboot(mute): # Performs a managed shutdown
	if mute.status() == "UNMUTED":
		current_time = datetime.now()
		wake_time = (current_time + timedelta(minutes=3)).strftime("%H:%M:%S")
		log.debug('sudo pmset repeat wakeorpoweron MTWRFSU {}'.format(wake_time))
		runProcess(["sudo", "pmset", "repeat", "wakeorpoweron", "MTWRFSU", "{}".format(wake_time)])
		log.info("Rebooting....")
		mute.mute()
		runProcess(["/bin/bash", "/Local/scripts/powerControl.sh", "shutdown"])
	else:
		log.info("Reboots Muted")


## Main ##
#######################################################


if __name__ == "__main__":

	# Initialize Variables
	statusRX0, statusRX1, statusTX0, statusTX1, statusInput = True, True, True, True, True
	expectedRx0, expectedRx1, expectedTx0, expectedTx1, expectedInput = "", "", "", "", ""
	outRX0, outRX1, outTX0, outTX1, outInput = "", "", "", "", ""

	# Initialize class objects
	integral = integralInterface(args.serial, interpreter, serialScriptPath)
	integralSerial = integralSerialInterface(integral)
	alertMute = muteFiles("integralCheck{}.mute".format(str(args.serial).split('-')[1]))
	rebootMute = muteFiles("integralReboot{}.mute".format(str(args.serial).split('-')[1]))
	connected = integralSerial.checkArg(args.serial)


	if connected == False:
		issueTime = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
		alertMessage = "Issue Time: {}  -  The serial device '{}', is not seen as an available serial device. Unable to communicate with Integral".format(issueTime,args.serial)
		alertEvent(alertMessage)
		alertEmail(alertMessage, alertMute) if args.notify else log.info("Not Alerting")
		exit(1)
	comm, rebootAvaliable = integralSerial.checkComm(args.serial)
	if comm == False:
		issueTime = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
		alertMessage = "Issue Time: {}  -  The computer failed to communicate with the integral serial device - '{}'. This could mean that communication was temporarily interrupted or a serial connection is disconnected".format(issueTime,args.serial)
		alertEvent(alertMessage)
		alertEmail(alertMessage, alertMute) if args.notify else log.info("Not Alerting")
		exit(1)


	# Main Loop
	if not args.interrogate:

		# fixMethod
		fixMethod = 'integral power cycle(s)' if rebootAvaliable else 'hotplug'
		log.info("Setting {} as fix method".format(fixMethod))

		# Whether to run command once or multiple tries
		tryNum = (args.tries) if args.fix == False else 0

		# Start Loop
		while tryNum <= args.tries:
			if args.rx0:
				expectedRx0 = args.rx0
				statusRX0, outRX0, errRX0 = integral.compare(expectedRx0, "getRX0")
			if args.rx1:
				expectedRx1 = args.rx1
				statusRX1, outRX1, errRX1 = integral.compare(expectedRx1, "getRX1")
			if args.tx0:
				expectedTx0 = args.tx0
				statusTX0, outTX0, errTX0 = integral.compare(expectedTx0, "getTX0")
			if args.tx1:
				expectedTx1 = args.tx1
				statusTX1, outTX1, errTX1 = integral.compare(expectedTx1, "getTX1")
			if args.input:
				expectedInput = args.input
				statusInput, outInput, errInput = integral.compare(expectedInput, "getInput")

			
			# Array of expected and measured results
			expected = [expectedRx0 , expectedRx1, expectedTx0, expectedTx1]
			measured = [outRX0, outRX1, outTX0, outTX1]
			log.debug("Expected: {}".format(expected))
			log.debug("Measured: {}".format(measured))

			tryNum+=1

			# Determine is there is any bad status
			if (statusRX0 == False or statusRX1 == False or statusTX0 == False or statusTX1 == False or statusInput == False) and (tryNum <= args.tries):
				if args.fix:
					if statusInput == False:
						commandDict = {"bot":"setInputBottom", "top":"setInputTop", "thru":"setInputThru", "swap":"setInputSwap"}
						command = commandDict[args.input]
						log.info("Switching Input Mode to {}".format(command))
						integral.runProcess([interpreter, serialScriptPath, args.serial, command])
						time.sleep(5)
						integral.hotplug(tryNum, args.tries)
					else:
						if rebootAvaliable:
							integral.restart(tryNum, args.tries)
						else:
							integral.hotplug(tryNum, args.tries)

			elif ((statusRX0 and statusRX1 and statusTX0 and statusTX1 and statusInput) != False):
				log.info("No Issues")
				alertMute.unMute()
				rebootMute.unMute()
				exit(0)

		else:
			# Determine Corrective Action based on input arguments
			issueTime = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
			if not args.fix:
				if args.reboot:
					log.info("Issue Detected - No {} attempted".format(fixMethod))
					alertMessage = "Issue Time: {}  -  Signal Issue detected - {} were skipped and the corrective action was escalated directly to managed shutdown. Rebooting in attempt to fix. Expected Signal: {} || Measured Signal {}".format(issueTime, fixMethod, expected,measured)
					alertMessageFailed = "Issue Time: {}  -  Signal Issue detected - {} were skipped and the corrective action was escalated directly to managed shutdown, but the issue was not resolved. Expected Signal: {} || Measured Signal {}".format(issueTime, fixMethod, expected,measured)
					#notify(alertMessage, alertMute) if args.notify else log.info('Not Alerting')
					alertEvent(alertMessage)
					if rebootMute.status() == "MUTED":
						alertEvent(alertMessageFailed)
						alertEmail(alertMessageFailed, alertMute) if args.notify else log.info("Not Alerting")
					reboot(rebootMute)
				else:
					log.info("Issue Detected - No {} attempted".format(fixMethod))
					alertMessage = "Issue Time: {}  -  Signal Issue detected, but the script was run without corrective action privledges. Expected Signal: {} || Measured Signal {}".format(issueTime,expected,measured)
					#notify(alertMessage, alertMute) if args.notify else log.info('Not Alerting')
					alertEvent(alertMessage)
					alertEmail(alertMessage, alertMute) if args.notify else log.info("Not Alerting")

			elif args.fix:
				if args.reboot:
					log.info("Failed to Resolve - attempting to Reboot")
					alertMessage = "Issue Time: {}  -  Signal Issue detected, but failed to resolve even after attempting {}. Performing a managed shutdown in attempt to fix. Expected Signal: {} || Measured Signal {}".format(issueTime, fixMethod, expected,measured)
					alertMessageFailed = "Issue Time: {}  -  Signal Issue detected, but failed to resolve even after attempting {}. Performing a managed shutdown did not resolve. Expected Signal: {} || Measured Signal {}".format(issueTime, fixMethod, expected,measured)
					alertEvent(alertMessage)
					if rebootMute.status() == "MUTED":
						#notify(alertMessage, alertMute) if args.notify else log.info('Not Alerting')
						alertEvent(alertMessageFailed)
						alertEmail(alertMessageFailed, alertMute) if args.notify else log.info("Not Alerting")
					reboot(rebootMute)
				else:
					log.info("Failed to Resolve - standing down")
					alertMessage = "Issue Time: {}  -  Signal Issue detected, but failed to resolve even after attempting {}. Standing Down. Expected Signal: {} || Measured Signal {}".format(issueTime, fixMethod, expected,measured)
					#notify(alertMessage, alertMute) if args.notify else log.info('Not Alerting')
					alertEvent(alertMessage)
					alertEmail(alertMessage, alertMute) if args.notify else log.info("Not Alerting")


###############################################################

	# Alternative Function
	elif args.interrogate:

		allCommands = ["getVersion", "getScale", "getInput", "getRX0", "getRX1", "getTX0", "getTX1", "getTX0Sink", "getTX1Sink"]
		label = ["VERSION", "SCALING", "INPUT PORT", "INP0 SIGNAL", "INP1 SIGNAL", "OUT0 SIGNAL", "OUT1 SIGNAL", "OUT0 EDID", "OUT1 EDID"]
		for command in allCommands:
			run = [interpreter, serialScriptPath, args.serial, command]
			results = runProcess(run)
			if label[allCommands.index(command)]:
				log.info(label[allCommands.index(command)] + " :: " + results[0])
			else:
				log.info(results[0])
		exit(0)


###############################################################