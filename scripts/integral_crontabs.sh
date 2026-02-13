#!/bin/bash

serial=$1

echo Standard Mirror EDID
echo " "
echo "# Verifies i/o resolutions of Integral"
echo "@reboot /bin/sleep 95; python /Local/scripts/integralStatus.py --serial /dev/tty.usbserial-$serial --rx0 \"4K60 444\" --tx0 \"4K60 444\" --input \"bot\" --fix --notify --reboot"
echo " "
echo " "
echo Dock
echo " "
echo "# Verifies i/o resolutions of Dock Integral"
echo "@reboot /bin/sleep 95; python /Local/scripts/integralStatus.py --serial /dev/tty.usbserial-$serial --rx0 \"1080P60 444\" --input \"bot\" --fix --notify --reboot"
echo " "
echo " "
echo Matrix Mode
echo " "
echo "# Verifies i/o resolutions of Dual Integral"
echo "@reboot /bin/sleep 95; python /Local/scripts/integralStatus.py --serial /dev/tty.usbserial-$serial --rx0 \"4K60 444\" --rx1 \"4K60 444\" --input \"thru\" --notify --reboot"