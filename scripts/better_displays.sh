#!/bin/bash
#set -euo pipefail

# Exit if arguments are not provided
if [ -z "${1-}" ] || [ -z "${2-}" ]; then
  echo "Error: Missing arguments for placement and screen count." >&2
  exit 1
fi

placement=$1
plist_path="/Users/t1user/Library/LaunchAgents/com.t1v.betterdisplay.plist"

echo "--- Starting BetterDisplay Setup ---"

# 1. Clean up previous state to prevent 'Input/output' errors
if launchctl list | grep -q "com.t1v.betterdisplay"; then
    echo "Service already loaded. Unloading..."
    launchctl unload -w "$plist_path" 2>/dev/null || true
    sleep 1
fi

# 2. Copy the plist
echo "Copying launch agent plist..."
cp /Local/scripts/com.t1v.betterdisplay.plist "$plist_path" || { echo "Failed to copy plist." >&2; exit 1; }

# 3. Load the agent (This starts the App)
echo "Loading launch agent..."
launchctl load -w "$plist_path" || { echo "Failed to load launch agent." >&2; exit 1; }

BETTER_DISPLAY_CMD=~/T1VApps/BetterDisplay.app/Contents/MacOS/BetterDisplay

# 4. Wait for the app to actually launch
echo "Waiting for BetterDisplay to initialize..."
max_retries=30
counter=0

while ! pgrep -f "BetterDisplay" > /dev/null; do
    sleep 1
    counter=$((counter+1))
    if [ $counter -ge $max_retries ]; then
        echo "Error: Timed out waiting for BetterDisplay to launch." >&2
        exit 1
    fi
done

echo "App process found. Giving it 5 seconds to warm up..."
sleep 5

# 5. Run Configuration Commands
echo "Applying configurations..."
# We allow the 'create' command to fail (|| true) in case the screen already exists from a previous run
"$BETTER_DISPLAY_CMD" create -devicetype=virtualscreen -virtualscreenname=VC1 -aspectWidth=16 -aspectHeight=9 -useResolutionList=on -resolutionList=1280x720 -virtualScreenVendorNumber=1 -virtualScreenModelNumber=1 -virtualScreenSerial=1 || echo "Note: Virtual screen might already exist."
if [ $? -eq 1 ]; then
  echo "Virtual screen creation failed."
fi
"$BETTER_DISPLAY_CMD" set -name=VC1 -connected=on
echo "Setting 720 resolution..."
"$BETTER_DISPLAY_CMD" set -name=VC1 -resolution=1280x720
if [ $? -eq 1 ]; then
  echo "Failed to set resolution."
fi
echo "Setting HiDPI..."
"$BETTER_DISPLAY_CMD" set -name=VC1 -hiDPI=off
if [ $? -eq 1 ]; then
  echo "Failed to set HiDPI."
fi
echo "Setting placement..."
"$BETTER_DISPLAY_CMD" set -name=VC1 -placement="$placement"
if [ $? -eq 1 ]; then
  echo "Failed to set placement."
fi

defaults write pro.betterdisplay.BetterDisplay SUAutomaticallyUpdate -bool false
defaults write pro.betterdisplay.BetterDisplay SUEnableAutomaticChecks -bool false

echo "BetterDisplay setup complete."
exit 0