def MSCconvertToHex(numASCII):
	'''lookup table to convert numbers to ASCII Hex Values for Midi Show Control'''
	if numASCII == '0':
		return 48
	elif numASCII == '1':
		return 49
	elif numASCII == '2':
		return 50
	elif numASCII == '3':
		return 51
	elif numASCII == '4':
		return 52
	elif numASCII == '5':
		return 53
	elif numASCII == '6':
		return 54
	elif numASCII == '7':
		return 55
	elif numASCII == '8':
		return 56
	elif numASCII == '9':
		return 57
	elif numASCII == '.':
		return 46
	elif numASCII == '-':
		return 0
	elif numASCII == ' ':
		return 32


def MSCCmdTypeLookup(cmd):
	''' Command MSC Hex Value Lookup table'''
	cmd = cmd.upper()
	if cmd == 'OPEN':
		return 27
	elif cmd == 'GO':
		return 1
	elif cmd == 'STOP':
		return 2
	elif cmd == 'RESUME':
		return 3
	elif cmd == 'CLOSE':
		return 28
	elif cmd == 'ALL_OFF':
		return 8
	elif cmd == 'GO_OFF':
		return 11
	else:
		print("Command not Supported")
		return None


def buildMscList(cmd, number, devId, cmdFormat):
	'''returns a list of hex values in MSC Sysex order. Calls MSCCmdTypeLookup() and
		#MSCconvertToHex().'''
	mscData = []
	mscData.append(240) #Start 
	mscData.append(127) #ALL-CALL
	mscData.append(int(devId))#Device ID. 
	mscData.append(2)#MSC
	mscData.append(cmdFormat)#Msc Data Format
	mscData.append(MSCCmdTypeLookup(cmd)) #Command
	for char in number: #Number, seperated by character
		mscData.append(MSCconvertToHex(char))
	mscData.append(247) #End
	return mscData


def processAndSend(data, devID, cmdFormat):
	''' Takes properly formatted command string and splits the command and number, 
		then calls buildMscList(), and returns that message'''
	cmdType, cmdNumber = data.split(":")   #Split data into command and numbers
	return(buildMscList(cmdType, cmdNumber, devID, cmdFormat))

