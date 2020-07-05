#MSCconvertToHex(): lookup table to convert numbers to ASCII Hex Values for Midi Show Control
def MSCconvertToHex(numASCII):
	if numASCII == '0':
		return 0x30
	elif numASCII == '1':
		return 0x31
	elif numASCII == '2':
		return 0x32
	elif numASCII == '3':
		return 0x33
	elif numASCII == '4':
		return 0x34
	elif numASCII == '5':
		return 0x35
	elif numASCII == '6':
		return 0x36
	elif numASCII == '7':
		return 0x37
	elif numASCII == '8':
		return 0x38
	elif numASCII == '9':
		return 0x39
	elif numASCII == '.':
		return 0x2E
	elif numASCII == '-':
		return 0x00

#MSCCmdTypeLookup(): Command MSC Hex Value Lookup table
def MSCCmdTypeLookup(cmd):
	cmd = cmd.upper()
	if cmd == 'OPEN':
		return 0x1b
	elif cmd == 'GO':
		return 0x1
	elif cmd == 'STOP':
		return 0x2
	elif cmd == 'RESUME':
		return 0x3
	elif cmd == 'CLOSE':
		return 0x1c
	elif cmd == 'ALL_OFF':
		return 0x8
	elif cmd == 'GO_OFF':
		return 0x0b
	else:
		print("Command not Supported")
		return None

#buildMscList(): returns a list of hex values in MSC Sysex order. Calls MSCCmdTypeLookup() and
	#MSCconvertToHex().
def buildMscList(cmd, number, devId, cmdFormat):
	mscData = []
	mscData.append(int(0xf0)) #Start 
	mscData.append(int(0x7f)) #ALL-CALL
	mscData.append(int(devId))#Device ID. 
	mscData.append(int(0x02))#MSC
	mscData.append(int(cmdFormat, 16))#Msc Data Format
	mscData.append(int(MSCCmdTypeLookup(cmd))) #Command
	for char in number: #Number, seperated by character
		mscData.append(int(MSCconvertToHex(char)))
	mscData.append(int(0xf7)) #End
	return mscData

#processAndSend(): Takes properly formatted command string and splits the command and number, 
	#then calls buildMscList(), and returns that message
def processAndSend(data, devID, cmdFormat):
	#Check that this is a command
	if (data.find(':') != -1):
		cmdType, cmdNumber = data.split(":")   #Split data into command and numbers
		return(buildMscList(cmdType, cmdNumber, devID, cmdFormat))

