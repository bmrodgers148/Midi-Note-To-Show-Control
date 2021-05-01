import rtmidi
import os 
import json
import kivy
from kivy.app import App 
from kivy.config import Config 
from kivy.uix.screenmanager import ScreenManager, Screen, NoTransition 
from kivy.core.window import Window 
from kivy.uix.widget import Widget 
from kivy.properties import ObjectProperty
import midiProcess

class midi():  # Handles all Midi input, output, and processing
	def __init__(self):
		try:
			ConfigData_Filename = os.path.join(os.path.dirname(os.path.realpath(__file__)), "config.json")
			ConfigData_JSON = open(ConfigData_Filename).read()
			ConfigData = json.loads(ConfigData_JSON)
			self.MSCCmdFormat = int(ConfigData['MSCCmdFormat'], 16)
			self.MSCDeviceID = int(ConfigData['MSCDeviceID'])
			self.expandedMode = ConfigData['expandedMode']
			self.inPort = int(ConfigData['inPort'])
			self.outPort = int(ConfigData['outPort'])
			self.MAMSCMode = ConfigData['MAMSCMode']
			self.MA = ConfigData['MA']


		except Exception as e:
			print("EXCEPTION: Cannot load and parse Config.JSON File. Loading Default settings.")
			print(e)
			self.MSCCmdFormat = 0x01
			self.MSCDeviceID = '1'
			self.expandedMode = True
			self.outPort = 0
			self.inPort = 0
			self.MA = False
			self.MAMSCMode = 'Default'

			ConfigData_Filename = os.path.join(os.path.dirname(os.path.realpath(__file__)), "config.json")
			ConfigData = {}  
			ConfigData['MSCCmdFormat'] = hex(self.MSCCmdFormat)
			ConfigData['MSCDeviceID'] = self.MSCDeviceID
			ConfigData['expandedMode'] = self.expandedMode
			ConfigData['inPort'] = self.inPort
			ConfigData['outPort'] = self.outPort
			ConfigData['MA'] = self.MA
			ConfigData['MAMSCMode'] = self.MAMSCMode
			ConfigData_JSON = open(ConfigData_Filename, 'w')
			json.dump(ConfigData, ConfigData_JSON, indent=1)

		self.cmdLookup = ['', 'GO', 'Set Cuelist', 'OPEN', 'STOP', 'RESUME', 'CLOSE', 'ALL_OFF', 'GO_OFF']
		self.currentCuelist = 0
		#GrandMA2 Specific Functionality
		self.MAExecPage = 0
		self.MAModes = ['Default', 'Exec.Page', 'Exec Page']
		self.stopRepeats = True
		

		self.midiIn = rtmidi.MidiIn()
		self.midiOut = rtmidi.MidiOut()
		self.availableInPort = self.midiIn.get_ports()
		self.availableOutPort = self.midiOut.get_ports()
		try:
			self.midiIn.open_port(self.inPort)
			self.midiOut.open_port(self.outPort)
			self.midiIn.set_callback(self.processMidiIn)
		except:
			pass

	def processMidiIn(self, event, data=None):
		midiInMSG = event[0]
		channel = 99
		lastMsg = []
		if(self.stopRepeats):
			if(midiInMSG != lastMsg):
				lastMsg = midiInMSG
				message = midiInMSG
		else: 
			message = midiInMSG

		if(message[0] >=144 and message[0] <= 159): #check for NOTE ON Command
			msgType = 'NOTE_ON'
			channel = message[0] - 143
		elif(message[0] >=128 and message[0] <= 143): #check for NOTE OFF Command
			msgType = 'NOTE_OFF'
			channel = message[0] - 127	
		elif(message[0] >=176 and message[0] <= 191): #check for CONTROL_CHANGE Command
			msgType = 'CONTROL_CHANGE'
			channel = message[0] - 175	
		else:
			return

		if(channel < 9):  #Determines which function needs to be called based on channel
			if(self.MA):
				self.MAbuildCommand(channel, message[1], message[2], msgType, message)
			else:
				self.buildCommand(channel, message[1], message[2], msgType, message)
		elif(channel == 9):
			self.changeSettings(channel, message[1], message[2], msgType)
		else:
			return



	def MAbuildCommand(self, channel, note, velocity, msgType, inbound):
		number = (note * 128) + velocity
		if(channel == 2 and msgType == 'NOTE_ON'):
			if (self.MAMSCMode == 'Exec.Page'):
				self.currentCuelist = f'{note}.{velocity}'
			elif (self.MAMSCMode == 'Exec Page'):
				self.currentCuelist = f'{note} {velocity}'
			mainApp.home_page.currentCuelist.text = ("Current Executor: " + '[color=#4254f5]' + 
					str(self.currentCuelist)+ '[/color]')
		
		elif(channel != 2 and msgType == 'NOTE_ON'):
			if(self.MAMSCMode == 'Exec.Page' or self.MAMSCMode == 'Exec Page'):
				command = f'{self.cmdLookup[channel]}:{number}.000-{self.currentCuelist}'
			elif(self.MAMSCMode == 'Default'):
				#print('default')
				command = f'{self.cmdLookup[channel]}:{number}.000'
			MSCMsg = midiProcess.processAndSend(command, self.MSCDeviceID, self.MSCCmdFormat)
			self.midiOut.send_message(MSCMsg)
			print(inbound)
			print(MSCMsg)
			mainApp.home_page.lastMessageUpdate(msgType, channel, note, velocity, self.cmdLookup[channel], 
				inbound, MSCMsg, number, self.currentCuelist)

#buildCommand() : Builds the command that is sent to midiProcess.py to be converted to MSC
	def buildCommand(self, channel, note, velocity, msgType, inbound):
		if (self.expandedMode == True  and msgType == 'NOTE_ON'):
			number = (note * 128) + velocity

			if(channel == 2): #Set Current Cuelist
				self.currentCuelist = number
				mainApp.home_page.currentCuelist.text = ("Current Cuelist: " + '[color=#4254f5]' + 
					str(self.currentCuelist)+ '[/color]')

			else: #Sends MSC Commands
				if(self.cmdLookup[channel] == 'GO'):
					command = self.cmdLookup[channel] + ':'+ str(number) + '-' + str(self.currentCuelist)
				elif(self.cmdLookup[channel] == 'ALL_OFF'):
					command = self.cmdLookup[channel] + ':'+ str(number)
				else:
					command = self.cmdLookup[channel] + ':' + str(number) + '-' + str(number)
				MSCMsg = midiProcess.processAndSend(command, self.MSCDeviceID, self.MSCCmdFormat)
				self.midiOut.send_message(MSCMsg)
				print(inbound)

				print(MSCMsg)
				mainApp.home_page.lastMessageUpdate(msgType, channel, note, velocity, self.cmdLookup[channel], 
					inbound, MSCMsg, number, self.currentCuelist)
		
		elif (self.expandedMode == False and msgType == 'NOTE_ON'):
			if(channel == 2):
				pass
			else:
				if(self.cmdLookup[channel] == 'GO'):
					command = self.cmdLookup[channel] + ':'+ str(note) + '-' + str(velocity)
				elif(self.cmdLookup[channel] == 'ALL_OFF'):
					command = self.cmdLookup[channel] + ':'
				else:
					command = self.cmdLookup[channel] + ':' + str(note) + '-' + str(velocity)
				MSCMsg = midiProcess.processAndSend(command, self.MSCDeviceID, self.MSCCmdFormat)
				self.midiOut.send_message(MSCMsg)
				print(inbound)
				print(MSCMsg)
				mainApp.home_page.lastMessageUpdate(msgType, channel, note, velocity, self.cmdLookup[channel], inbound, MSCMsg, note, velocity)

#changeSettings() : proccesses program setting changes submitted on midi channel 9
	def changeSettings(self, channel, note, velocity, msgType):
		return

#kivyUpdateSettings(): Saves changes made in GUI and reopens midi ports using new selection.
	def kivyUpdateSettings(self, inPort, outPort, cmdFormat, expMode, devId, maMode, MAMSCMode='Default'):
		if(self.midiIn.is_port_open()):
			self.midiIn.close_port()
		if(self.midiOut.is_port_open()):
			self.midiOut.close_port()
		self.inPort = inPort
		self.outPort = outPort
		self.expandedMode = expMode
		self.MSCCmdFormat = int(cmdFormat, 16)
		self.MSCDeviceID = int(devId)
		self.MA = maMode
		self.MAMSCMode = MAMSCMode

		try:
			self.midiIn.open_port(self.inPort)
			self.midiOut.open_port(self.outPort)
			self.midiIn.set_callback(self.processMidiIn)
		except:
			pass


		#Update config.json with new settings
		ConfigData_Filename = os.path.join(os.path.dirname(os.path.realpath(__file__)), "config.json")
		ConfigData = {}  
		ConfigData['MSCCmdFormat'] = hex(self.MSCCmdFormat)
		ConfigData['MSCDeviceID'] = self.MSCDeviceID
		ConfigData['expandedMode'] = self.expandedMode
		ConfigData['inPort'] = self.inPort
		ConfigData['outPort'] = self.outPort
		ConfigData['MA'] = self.MA
		ConfigData['MAMSCMode'] = self.MAMSCMode
		ConfigData_JSON = open(ConfigData_Filename, 'w')
		json.dump(ConfigData, ConfigData_JSON, indent=1)

		#update home page with new info
		mainApp.home_page.updateLabels()


class HomePage(Widget): #Kivy Home Page
	inputPort = ObjectProperty(None)
	outputPort = ObjectProperty(None)
	expandedMode = ObjectProperty(None)
	currentCuelist = ObjectProperty(None)
	msgType = ObjectProperty(None)
	channel = ObjectProperty(None)
	note = ObjectProperty(None)
	command = ObjectProperty(None)
	mscdata = ObjectProperty(None)
	rawMidiIn = ObjectProperty(None)
	rawMidiOut = ObjectProperty(None)

#lastMessageUpdate(): Updates last message label on HomePage whennever a new midi message is recieved
	def lastMessageUpdate(self, type, ch, n, v, cmd, inbound, outbound, cue=0, cuelist=0):
		inboundHex = []
		outboundHex = []

		self.msgType.text = "Type: " + str(type)
		self.channel.text = f"Channel: [color=#4254f5]{ch}[/color]"
		self.note.text = ("Note: " + '[color=#4254f5]' + str(n)+ '[/color]'+ 
			"          Velocity: " + '[color=#4254f5]' + str(v)+ '[/color]'   )
		self.command.text = "Command: " + '[color=#4254f5]' + str(cmd)+ '[/color]'
		self.mscdata.text = ("Cue: " + '[color=#4254f5]' + str(cue)+ '[/color]' + "          Cuelist: "
			+ '[color=#4254f5]' + str(cuelist)+ '[/color]')
		
		#Convert integer lists to hex for raw midi in and out
		inboundString = ''
		outboundString = ''
		for x in inbound:
			inboundString += ('{:02X}'.format(x) + '  ')
		for y in outbound:
			outboundString += ('{:02X}'.format(y) + '  ')

		self.rawMidiIn.text = "Raw Midi In: " + '[color=#4254f5]' + str(inboundString)+ '[/color]'
		self.rawMidiOut.text = "Raw Midi Out: \n" + '[color=#4254f5]' + str(outboundString)+ '[/color]'
		print(self.msgType.text)
		print(self.channel.text)
		print(self.note.text)
		print(self.command.text)
		print(self.mscdata.text)
		print(self.rawMidiIn.text)
		print(self.rawMidiOut.text)
		print("_________________________________________\n")


#updateLabels(): Updates label text to relfect settings. Run at start, and by kivyUpdateSettings()
	def updateLabels(self):
		if (mainApp.midiSession.expandedMode):
			self.expandedMode.text = 'Expanded Mode [color=#42f54e]Enabled[/color]'
		else:
			self.expandedMode.text = 'Expanded Mode [color=#c40a0a]Disabled[/color]'

		#checks that ports are open, shows error if not.	
		if(mainApp.midiSession.midiIn.is_port_open() == False):
			self.inputPort.text = "[color=#c40a0a]INPUT PORT NOT CONNECTED[/color]"
		else:
			self.inputPort.text = "Input Port: \n" + mainApp.midiSession.availableInPort[mainApp.midiSession.inPort]
		if(mainApp.midiSession.midiOut.is_port_open() == False):
			self.outputPort.text = "[color=#c40a0a]OUTPUT PORT NOT CONNECTED[/color]"
		else:
			self.outputPort.text = "Output Port: \n" + mainApp.midiSession.availableOutPort[mainApp.midiSession.outPort]

		self.currentCuelist.text = "Current Cuelist: " + '[color=#4254f5]' + str(mainApp.midiSession.currentCuelist)+ '[/color]'


class SettingsPage(Widget): #Kivy Settings Page
	inSelect = ObjectProperty()
	outSelect = ObjectProperty(None)
	expSelect = ObjectProperty(None)
	cmdFormat = ObjectProperty(None)
	devID = ObjectProperty(None)
	maMode = ObjectProperty(None)

#createVars(): Run at startup, sets variables to starting value for spinners
	def createVars(self):
		self.newInPort = mainApp.midiSession.inPort
		self.newOutPort = mainApp.midiSession.outPort
		self.MAMSCMode = mainApp.midiSession.MAMSCMode

#inSpinnerSet(): Run when a new value is selected for inSpinner.
	def inSpinnerSet(self, value):
		self.newInPort = mainApp.midiSession.availableInPort.index(value)

#outSpinnerSet(): Run when a new value is selected for outSpinner.
	def outSpinnerSet(self, value):
		self.newOutPort = mainApp.midiSession.availableOutPort.index(value)

	def maModeSet(self, value):
		self.MAMSCMode = value 

#saveSettings(): Run by save settings button, fires kivyUpdateSettings in midi class to commit changes
	def saveSettings(self):
		mainApp.midiSession.kivyUpdateSettings(self.newInPort, self.newOutPort, str(self.cmdFormat.text),
			self.expSelect.active, self.devID.text, self.maMode.active, self.MAMSCMode)


class CalculatorPage(Widget): #Midi Calculator Page
	resultlabel = ObjectProperty(None)
	cueNum = ObjectProperty(None)
	cuelist = ObjectProperty(None)
	expMode = ObjectProperty(None)
	commandSelect = ObjectProperty(None)
	cmdSelTxt = 'GO'

#calculate(): Run by calculate button, takes outbound message wanted, and calculates inbound midi message
	def calculate(self):
		ch = mainApp.midiSession.cmdLookup.index(self.cmdSelTxt)
		cue = int(self.cueNum.text)
		cuelist = int(self.cuelist.text)

		#Calcualtions for expanded mode
		if(self.expMode.active):
			cuenote = int(cue / 128)
			cuevelocity = cue % 128
			cuelistnote = int(cuelist / 128)
			cuelistvelocity = cuelist % 128

			if(ch == 1): #Go Command
				self.resultlabel.text = (f"[b]Channel: [color=#4254f5]{ch}[/color]\n" 
					f"Note: [color=#4254f5]{cuenote}[/color]\n"
					f"Velocity: [color=#4254f5]{cuevelocity}[/color]\n\n"
					f"[color=#993333]NOTE: THIS COMMAND ONLY USES CUE NUMBER. YOU MUST SEND SET CUELIST COMMAND AT START OF NEW CUELIST![/color][/b]")
				self.resultlabel.font_size = 30

			elif(ch ==2): # Set Cuelist
				self.resultlabel.text = (f"[b]Channel: [color=#4254f5]{ch}[/color]\n" 
					f"Note: [color=#4254f5]{cuelistnote}[/color]\n"
					f"Velocity: [color=#4254f5]{cuelistvelocity}[/color]\n\n"
					f"[color=#993333]NOTE: THIS COMMAND ONLY USES CUELIST NUMBER. YOU MUST SEND SEPERATE GO COMMAND![/color][/b]")
				self.resultlabel.font_size = 30
			elif(ch >=3 and ch <=8): #Open, Stop, Resume, Close, all_off, Go_off
				self.resultlabel.text = (f"[b]Channel: [color=#4254f5]{ch}[/color]\n" 
					f"Note: [color=#4254f5]{cuelistnote}[/color]\n"
					f"Velocity: [color=#4254f5]{cuelistvelocity}[/color]\n\n"
					f"[color=#993333]NOTE: THIS COMMAND ONLY USES CUELIST NUMBER.[/color][/b]")
				self.resultlabel.font_size = 30
			else:
				self.resultlabel.text = '[b][color=#FF0000]AN ERROR HAS OCCURED[/b][/color]'
		#Calculations for simple mode
		else:
			#Checks for valid integer range. 
			if(cue < 128 and cuelist < 128):
				if(ch == 1): #Go Command
					self.resultlabel.text = (f"[b]Channel: [color=#4254f5]{ch}[/color]\n" 
						f"Note: [color=#4254f5]{cue}[/color]\n"
						f"Velocity: [color=#4254f5]{cuelist}[/color]\n\n"
						f"[color=#993333][/color][/b]")
					self.resultlabel.font_size = 30

				elif(ch ==2): # Set Cuelist
					self.resultlabel.text = ("[color=#FF0000]This command is only used in Expanded Mode. See readme for details[/color][/b]")
					self.resultlabel.font_size = 30
				elif(ch >=3 and ch <=8): #Open, Stop, Resume, Close, all_off, Go_off
					self.resultlabel.text = (f"[b]Channel: [color=#4254f5]{ch}[/color]\n" 
						f"Note: [color=#4254f5]{cue}[/color]\n"
						f"Velocity: [color=#4254f5]{cuelist}[/color]\n\n"
						f"[color=#993333]NOTE: THIS COMMAND ONLY USES CUELIST NUMBER.[/color][/b]")
					self.resultlabel.font_size = 30
				else:
					self.resultlabel.text = '[b][color=#FF0000]AN ERROR HAS OCCURED[/b][/color]'
			#If valid range is exceded, shows error to user
			else:
				self.resultlabel.text = ('[b][color=#FF0000]Values must be between 0 and 127. Use Expanded Mode for '
					'higher numbers. See readme for details.[/b][/color]')

#setCmdSelTxt(): run by command selection spinner, sets variable to new command selection for calculations
	def setCmdSelTxt(self, value):
		self.cmdSelTxt = value


class MidiApp(App): #Main App for Kivy
	def build(self):
		self.title = 'Midi Note to Show Control'
		self.midiSession = midi() #Create midi() object

		self.screen_manager = ScreenManager(transition=NoTransition()) #Create Screen Manager, No transition

		#Setup Home Page
		self.home_page = HomePage()
		screen = Screen(name="Home")
		screen.add_widget(self.home_page)
		self.screen_manager.add_widget(screen)
		self.home_page.updateLabels()

		#Setup Settings Page
		self.Settings_page = SettingsPage()
		self.Settings_page.createVars()
		screen = Screen(name="Settings")
		screen.add_widget(self.Settings_page)
		self.screen_manager.add_widget(screen)

		#Setup Calculator Page
		self.Calculator_page = CalculatorPage()
		screen = Screen(name="Calculator")
		screen.add_widget(self.Calculator_page)
		self.screen_manager.add_widget(screen)

		#Set Configuration and defaults for App
		Window.clearcolor = (.8,.8,.8,0)
		Window.size = (950, 475)
		self.screen_manager.current = 'Home'
		
		return self.screen_manager

	def settingsPage(self):
		self.screen_manager.current = 'Settings'

	def calculatorPage(self):
		self.screen_manager.current = 'Calculator'

	def homePage(self):
		self.screen_manager.current = 'Home'

#Create and Run App
if __name__ == "__main__":
	mainApp = MidiApp()
	#Set Window Configuration Settings
	#Config.set('graphics', 'resizable', 1)
	#Config.set('graphics', 'borderless', 0)
	Config.set('kivy', 'desktop', 1)
	Config.write()
	mainApp.run()

