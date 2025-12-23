#!/bin/bash

monitorD=`ps -ef | grep menumonitord | grep -v grep | wc -l`
if [ $monitorD == 1 ]; then
killall -USR1 menumonitord
else
killall -USR1 MenuMonitor
fi
