#!/bin/bash

serial=$1

defaults write com.t1visions.SerialScripts "Display 1" -dict-add "Name" "Main 4K Avocor"

defaults write com.t1visions.SerialScripts "Display 1" -dict-add "ExpectedSignal" "Signal Present"

defaults write com.t1visions.SerialScripts "Display 1" -dict-add "ExpectedPowerON" "Power On"

defaults write com.t1visions.SerialScripts "Display 1" -dict-add GetSignal "/usr/local/bin/python /Local/scripts/serial/AvocorH20.py $(ls /dev/tty.usbserial-$serial) GetSignal"

defaults write com.t1visions.SerialScripts "Display 1" -dict-add GetPower "/usr/local/bin/python /Local/scripts/serial/AvocorH20.py $(ls /dev/tty.usbserial-$serial) GetPower"

defaults write com.t1visions.SerialScripts "Display 1" -dict-add PowerOn "/usr/local/bin/python /Local/scripts/serial/AvocorH20.py $(ls /dev/tty.usbserial-$serial) PowerOn"

defaults write com.t1visions.SerialScripts "Display 1" -dict-add PowerOff "/usr/local/bin/python /Local/scripts/serial/AvocorH20.py $(ls /dev/tty.usbserial-$serial) PowerOff"

defaults write com.t1visions.SerialScripts "Display 1" -dict-add BacklightOn "/usr/local/bin/python /Local/scripts/serial/AvocorH20.py $(ls /dev/tty.usbserial-$serial) BacklightOn"

defaults write com.t1visions.SerialScripts "Display 1" -dict-add BacklightOff "/usr/local/bin/python /Local/scripts/serial/AvocorH20.py $(ls /dev/tty.usbserial-$serial) BacklightOff"

defaults write com.t1visions.SerialScripts "Display 1" -dict-add VolumeMute "/usr/local/bin/python /Local/scripts/serial/AvocorH20.py $(ls /dev/tty.usbserial-$serial) VolumeMute"

defaults write com.t1visions.SerialScripts "Display 1" -dict-add VolumeUnmute "/usr/local/bin/python /Local/scripts/serial/AvocorH20.py $(ls /dev/tty.usbserial-$serial) VolumeUnmute"

defaults write com.t1visions.SerialScripts "Display 1" -dict-add GetInput "/usr/local/bin/python /Local/scripts/serial/AvocorH20.py $(ls /dev/tty.usbserial-$serial) GetInput"

defaults write com.t1visions.SerialScripts "Display 1" -dict-add HDMI1 "/usr/local/bin/python /Local/scripts/serial/AvocorH20.py $(ls /dev/tty.usbserial-$serial) HDMI1"

defaults write com.t1visions.SerialScripts "Display 1" -dict-add HDMI2 "/usr/local/bin/python /Local/scripts/serial/AvocorH20.py $(ls /dev/tty.usbserial-$serial) HDMI2"

defaults write com.t1visions.SerialScripts "Display 1" -dict-add RC_Menu "/usr/local/bin/python /Local/scripts/serial/AvocorH20.py $(ls /dev/tty.usbserial-$serial) RC_Menu"
