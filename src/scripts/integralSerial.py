#!/usr/bin/env python
import serial
import subprocess
import time
import sys
import time
 

### speed enhanced version


commands = {
    "reboot": "set reboot on",
    "getVersion": "get ver",
    "getRX0": "get status rx0",
    "getRX1": "get status rx1",
    "getTX0": "get status tx0",
    "getTX1": "get status tx1",
    "getTX0Sink": "get status tx0sink",
    "getTX1Sink": "get status tx1sink",
    "getAudio0": "get status aud0",
    "getAudioMode0": "get audiochbot",
    "getAudioMode1": "get audiochtop",
    "getAudio1": "get status aud1",
    "sendHotplug": "set hotplug",
    "getInput": "get input",
    "setInputTop": "set input top",
    "setInputBottom": "set input bot",
    "setInputThru": "set input thru",
    "setInputSwap": "set input swap",
    "setInput0": "set input 0",
    "setInput1": "set input 1",
    "getHDCP": "get hdcp",
    "getAutoSwitch" : "get autosw",
    "setAutoSwitchOn" : "set autosw on",
    "setAutoSwitchOff" : "set autosw off",
    "getAutoSwitchPriority": "get autoswprio",
    "setAutoSwitchPriorityOn": "set autoswprio on",
    "setAutoSwitchPriorityOff": "set autoswprio off",
    "getScale": "get scale",
    "setScalingAuto": "set scale auto",
    "setScalingCustom": "set scale custom",
    "setScalingNone": "set scale none",
    "getHDCPSwitchPos": "get hdcpswitchpos",
    "getHDCPMode": "get hdcp",
    "setHDCP14": "set hdcp 14",
    "setHDCP22": "set hdcp 22",
    "getEdidSwitchPos": "get edidswitchpos",
    "getEdidMode": "get edidmode",
    "setEdidModeCustom" : "set edidmode custom",
    "setEdidModeAuto" : "set edidmode automix",
    "setEdidModeFixed" : "set edidmode fixed",
    "setEdidModeCopyOutput0" : "set edidmode copybot",
    "setEdidModeCopyOutput1" : "set edidmode copytop",
    "getEdidTableInput0": "get edidtable",
    "getEdidTableInput1": "get edidtabletop",
    "getEdidAlgorithm" : "get edidalgo",
    "setEdidAlgoMAX": "set edidalgo 4",
    "setEdidAlgoInput0Priority": "set edidalgo 2",
    "setEdidAlgoInput1Priority": "set edidalgo 3",
    "getOsdState": "get osd",
    "setOsdOn": "set osd on",
    "setOsdOff": "set osd off",
    "getOsdFadeValue": "get osdfadevalue",
    "getLED": "get logoled",
    "setLEDOn": "set logoled on",
    "setLEDOff": "set logoled off",
    "getCEC": "get cec",
    "setCECOn": "set cec on",
    "setCECOff": "set cec off",
    "getMute": "get mutebotaudio",
    "Mute":"set mutebotaudio on", 
    "UnMute": "set mutebotaudio off",
    # EDID Commands
    "setEDIDTableInput1" : "set edidtable 1",	# Blank / Custom
    "setEDIDTableInputTop1" : "set edidtabletop 1",
    "setEDIDTableInput2" : "set edidtable 2",	# Hardware VC
    "setEDIDTableInputTop2" : "set edidtabletop 2",
    "setEDIDTableInput3" : "set edidtable 3",	# 1080 Dock 1
    "setEDIDTableInputTop3" : "set edidtabletop 3",
    "setEDIDTableInput4" : "set edidtable 4",	# 1080 Dock 2
    "setEDIDTableInputTop4" : "set edidtabletop 4",
    "setEDIDTableInput5" : "set edidtable 5",	# 4K Dock 1
    "setEDIDTableInputTop5" : "set edidtabletop 5",
    "setEDIDTableInput6" : "set edidtable 6",	# 4K Dock 2
    "setEDIDTableInputTop6" : "set edidtabletop 6",
    "setEDIDTableInput7" : "set edidtable 7",	# Main 4K 1
    "setEDIDTableInputTop7" : "set edidtabletop 7",
    "setEDIDTableInput8" : "set edidtable 8",	# Main 4K 2
    "setEDIDTableInputTop8" : "set edidtabletop 8",
    "setEDIDTableInput9" : "set edidtable 9",	# Main 4K 3
    "setEDIDTableInputTop9" : "set edidtabletop 9",
    "setEDIDTableInput10" : "set edidtable 10",	# Main 4K - Standard
    "setEDIDTableInputTop10" : "set edidtabletop 10", 
    "setEDIDTableInput19" : "set edidtable 19", # Default Built-In 4K (4K60-444 600MHz Stereo)
    "setEDIDTableInputTop19" : "set edidtabletop 19",
    "setEDIDTableInput31" : "set edidtable 31", # 4K60-420 12bit HDR BT2020 Stereo
    "setEDIDTableInputTop31" : "set edidtabletop 31",
    "setEDIDTableInput37" : "set edidtable 37", # 4K60-420 12bit Stereo
    "setEDIDTableInputTop37" : "set edidtabletop 37",
    "setEDIDTableInput40" : "set edidtable 40", # 4K60-420 8-bit 300MHz HDR BT2020 Stereo
    "setEDIDTableInputTop40" : "set edidtabletop 40",
    "setEDIDTableInput46" : "set edidtable 46", # 4K60-420 8-bit 300MHz Stereo
    "setEDIDTableInputTop46" : "set edidtabletop 46",
}

interrogate = [
    ("VERSION", "getVersion"),
    ("SCALING", "getScale"),
    ("INPUT PORT", "getInput"),
    ("INP0 SIGNAL", "getRX0"),
    ("INP1 SIGNAL", "getRX1"),
    ("OUT0 SIGNAL", "getTX0"),
    ("OUT1 SIGNAL", "getTX1"),
    ("OUT0 EDID", "getTX0Sink"),
    ("OUT1 EDID", "getTX1Sink"),
    ("BOT EDID TABLE", "getEdidTableInput0"),
    ("TOP EDID TABLE", "getEdidTableInput1"),
]

######## Get Input Arguments ###########




######### Initialize Serial Connection ##########

def _send(ser, raw):
    ser.reset_input_buffer()
    ser.write(f"#{raw}\r".encode())
    buf = bytearray()
    deadline = time.time() + ser.timeout
    while time.time() < deadline:
        chunk = ser.read(ser.in_waiting or 1)
        if not chunk:
            continue
        buf.extend(chunk)
        if b"\r" in chunk or b"\n" in chunk:
            break
    return buf.decode(errors="replace").strip()


def _interrogate(ser):
    for label, command_key in interrogate:
        raw = _send(ser, commands[command_key])
        print(f"{label} :: {raw}")


def main():
    if len(sys.argv) < 3:
        sys.exit("/Users/t1user/serial/scripts/integralSerial.py <usbserial port name> <command>")
    else:
        portName = sys.argv[1]
        input = sys.argv[2]

    if input not in commands and input != "interrogate":
        print("Invalid command selected. Valid commands are:\n" + str(commands.keys()).replace(",", "\n").replace("'", ""))
        sys.exit(1)

    ser = serial.Serial(portName, 9600, parity='N', stopbits=1, bytesize=8, timeout=2, writeTimeout=2)
    time.sleep(0.1)

    try:
        if input == "interrogate":
            _interrogate(ser)
        else:
            resp =_send(ser, commands[input])
            print(resp)
    finally:
        ser.close()
    
if __name__ == "__main__":
    main()
