#!/bin/bash

serial=$1

defaults write com.t1visions.SerialScripts "Display 1" -dict-add "Name" "Main 4K Avocor"

defaults write com.t1visions.SerialScripts "Display 1" -dict-add "ExpectedPowerON" "Power On"

defaults write com.t1visions.SerialScripts "Display 1" -dict-add GetPower "/usr/local/bin/python /Local/scripts/serial/AvocorE50.py $(ls /dev/tty.usbserial-$serial) GetPower"

defaults write com.t1visions.SerialScripts "Display 1" -dict-add PowerOn "/usr/local/bin/python /Local/scripts/serial/AvocorE50.py $(ls /dev/tty.usbserial-$serial) PowerOn"

defaults write com.t1visions.SerialScripts "Display 1" -dict-add PowerOff "/usr/local/bin/python /Local/scripts/serial/AvocorE50.py $(ls /dev/tty.usbserial-$serial) PowerOff"

defaults write com.t1visions.SerialScripts "Display 1" -dict-add GetButtonLock "/usr/local/bin/python /Local/scripts/serial/AvocorE50.py $(ls /dev/tty.usbserial-$serial) GetButtonLock"

defaults write com.t1visions.SerialScripts "Display 1" -dict-add ButtonLockOff "/usr/local/bin/python /Local/scripts/serial/AvocorE50.py $(ls /dev/tty.usbserial-$serial) ButtonLockOff"

defaults write com.t1visions.SerialScripts "Display 1" -dict-add ButtonLockOn "/usr/local/bin/python /Local/scripts/serial/AvocorE50.py $(ls /dev/tty.usbserial-$serial) ButtonLockOn"

defaults write com.t1visions.SerialScripts "Display 1" -dict-add GetMute "/usr/local/bin/python /Local/scripts/serial/AvocorE50.py $(ls /dev/tty.usbserial-$serial) GetMute"

defaults write com.t1visions.SerialScripts "Display 1" -dict-add GetVolume "/usr/local/bin/python /Local/scripts/serial/AvocorE50.py $(ls /dev/tty.usbserial-$serial) GetVolume"

defaults write com.t1visions.SerialScripts "Display 1" -dict-add HDMI1 "/usr/local/bin/python /Local/scripts/serial/AvocorE50.py $(ls /dev/tty.usbserial-$serial) HDMI1"

defaults write com.t1visions.SerialScripts "Display 1" -dict-add HDMI2 "/usr/local/bin/python /Local/scripts/serial/AvocorE50.py $(ls /dev/tty.usbserial-$serial) HDMI2"

defaults write com.t1visions.SerialScripts "Display 1" -dict-add HomeScreen "/usr/local/bin/python /Local/scripts/serial/AvocorE50.py $(ls /dev/tty.usbserial-$serial) HomeScreen"

defaults write com.t1visions.SerialScripts "Display 1" -dict-add Reset "/usr/local/bin/python /Local/scripts/serial/AvocorE50.py $(ls /dev/tty.usbserial-$serial) Reset"

