serial=$1

defaults write com.t1visions.SerialScripts "Display 1" -dict-add "Name" "Main 4K Avocor"

defaults write com.t1visions.SerialScripts "Display 1" -dict-add "ExpectedPowerON" "Power On"

defaults write com.t1visions.SerialScripts "Display 1" -dict-add "ExpectedSignal" "Signal Present"

defaults write com.t1visions.SerialScripts "Display 1" -dict-add OFF "/usr/local/bin/python /Local/scripts/serial/AvocorG60.py $(ls /dev/tty.usbserial-$serial) BacklightOff";

defaults write com.t1visions.SerialScripts "Display 1" -dict-add ON "/usr/local/bin/python /Local/scripts/serial/AvocorG60.py $(ls /dev/tty.usbserial-$serial) BacklightOn";

defaults write com.t1visions.SerialScripts "Display 1" -dict-add GetBacklight "/usr/local/bin/python /Local/scripts/serial/AvocorG60.py $(ls /dev/tty.usbserial-$serial) GetBackLight";

defaults write com.t1visions.SerialScripts "Display 1" -dict-add GetPower "/usr/local/bin/python /Local/scripts/serial/AvocorG60.py $(ls /dev/tty.usbserial-$serial) GetPower";

defaults write com.t1visions.SerialScripts "Display 1" -dict-add GetFirmware "/usr/local/bin/python /Local/scripts/serial/AvocorG60.py $(ls /dev/tty.usbserial-$serial) GetFirmware";

defaults write com.t1visions.SerialScripts "Display 1" -dict-add SetInput "/usr/local/bin/python /Local/scripts/serial/AvocorG60.py $(ls /dev/tty.usbserial-$serial) HDMI2";

defaults write com.t1visions.SerialScripts "Display 1" -dict-add LockKeys "/usr/local/bin/python /Local/scripts/serial/AvocorG60.py $(ls /dev/tty.usbserial-$serial) LockKeys";

defaults write com.t1visions.SerialScripts "Display 1" -dict-add UnlockKeys "/usr/local/bin/python /Local/scripts/serial/AvocorG60.py $(ls /dev/tty.usbserial-$serial) UnlockKeys";
