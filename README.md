# Midi-Note-To-Show-Control
 Python program to convert midi notes to midi show control

#Introduction:
This is a simple python program that takes incoming Midi Notes and converts them to Midi Show Control based on certain criteria. 
This program was designed for house of worship and other similar applications where lighting automation is needed using midi notes, 
but with a lighting console that only accepts midi show control. This program is designed as a bridge between software such as ProPresenter, Ableton Live, 
Loop Community Prime, and Multitracks.com Playback and Lighting consoles. 


#How it works:
After setting the input and output midi ports, the program listens for Note On commands on the Input Port. When it detects a Note on message, it then parses the data and generates a Midi Show Control Command, which is then sent out to the Output Port designated.


#Simple vs. Expanded Mode:
Due to the limitation of midi, the note and velocity parts of a note on command are limited to 128 values. This severely limits the usability, as every cue and cuelist number in the lighting console would have to be below 128. This is why there are 2 modes. 

Expanded Mode: This mode uses both the note and velocity together to give a range of values from 0 to 16384. This works the same way as 16-bit dmx Channels, where the note value would be the coarse channel, and velocity would be the fine channel. The formula in the code is Number = Note * 128 + Velocity. Examples: For a final number of 200, note would be 1, velocity would be 72. A note of 0, and a velocity of 25, would equal a final number of 25. In expanded mode, you must send the cuelist number on Channel 2 Prior to sending the cue numbers on channel 1. The cuelist number is saved until a new cuelist number is sent, so you only have to send it once for multiple go commands in the same list. 

Simple Mode: This mode is limited to 127 cues and cuelists, but it allows for cue and cuelist to be sent with one note on message. In this mode, the Note would be the cue number, and velocity would be the cuelist.


#Choosing a command type: 
The command type is determined by the Channel of the incoming midi message. The channels and Command types are as follows:
Channel 1: GO
Channel 2: Not MSC. This channel is used to choose a cuelist in expanded mode
Channel 3: OPEN.   This command only requires a cuelist number. In simple mode, the note value is ignored.
Channel 4: STOP.   This command only requires a cuelist number. In simple mode, the note value is ignored.
Channel 5: RESUME. This command only requires a cuelist number. In simple mode, the note value is ignored.
Channel 6: CLOSE.  This command only requires a cuelist number. In simple mode, the note value is ignored.
Channel 7: ALL_OFF. This command ignores note and velocity.
Channel 8: GO_OFF. This command only requires a cuelist number. In simple mode, the note value is ignored.
Channel 9 is reserved for program setting changes.
Channels 10-16 are not used by this program.