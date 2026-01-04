#!/bin/bash
set -euo pipefail

# Exit if arguments are not provided
if [ -z "${1-}" ] || [ -z "${2-}" ]; then
  echo "Error: Missing arguments for placement and screen count." >&2
  exit 1
fi

placement=$1


cp /Local/scripts/com.t1v.betterdisplay.plist /Users/t1user/Library/LaunchAgents/ || { echo "Failed to copy plist." >&2; exit 1; }

launchctl load -w /Users/t1user/Library/LaunchAgents/com.t1v.betterdisplay.plist || { echo "Failed to load launch agent." >&2; exit 1; }

BETTER_DISPLAY_CMD=~/T1VApps/BetterDisplay.app/Contents/MacOS/BetterDisplay

$BETTER_DISPLAY_CMD create -devicetype=virtualscreen -virtualscreenname=VC1 -aspectWidth=16 -aspectHeight=9 -useResolutionList=on -resolutionList=1280x720 -virtualScreenVendorNumber=1 -virtualScreenModelNumber=1 -virtualScreenSerial=1
$BETTER_DISPLAY_CMD set -name=VC1 -connected=on
$BETTER_DISPLAY_CMD set -name=VC1 -resolution=1280x720
$BETTER_DISPLAY_CMD set -name=VC1 -hiDPI=off
$BETTER_DISPLAY_CMD set -name=VC1 -placement="$placement"

defaults write pro.betterdisplay.BetterDisplay SUAutomaticallyUpdate -bool false
defaults write pro.betterdisplay.BetterDisplay SUEnableAutomaticChecks -bool false

echo "BetterDisplay setup complete."
exit 0