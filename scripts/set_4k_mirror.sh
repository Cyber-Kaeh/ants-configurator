#!/bin/bash

serial_id=$1

python /Local/scripts/serial/integralSerial.py /dev/tty.usbserial-$serial_id setScalingNone

python /Local/scripts/serial/integralSerial.py /dev/tty.usbserial-$serial_id reboot

echo "Done."
