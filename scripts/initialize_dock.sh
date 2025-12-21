#!/bin/bash

placement=$1
names=$2

echo "defaults write enableDock 1"

echo "defaults write dock-position \"$placement, 0, 1920, 1080\""

echo "defaults write dock-names \"$names\""