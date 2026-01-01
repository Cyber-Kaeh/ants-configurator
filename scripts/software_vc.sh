#!/bin/bash

screens="$1"
choice="$2"
screen_placement="$3"
screen_height="$4"

echo "Choice: $choice"
echo "Screen placement: $screen_placement"
echo "Screen height: $screen_height"


if [[ "$screens" == 1 ]]; then
    echo "Running defaults for single display setup."
    defaults write com.t1visions.TTMenu screenUpdateOnAllChanges 1
    defaults write com.t1visions.TTMenu desktopMoveAllWindows 1
elif [[ "$screens" == 2 ]]; then
    echo "Running defaults for multi display setup."
    defaults write com.t1visions.TTMenu desktopMoveAllWindows 1
    defaults write com.t1visions.TTMenu thinkHubDesktopScreenRect -string "{{xx, xx}, {1280, 720}}"
    defaults write com.t1visions.TTMenu thinkHubDesktopThinkHubScreenIndex 0
else
    echo "Invalid number of screens: $screens"
    exit 1
fi

if [[ "$choice" == "zoom" ]]; then
    echo "Enabling Zoom with screen placement $screen_placement"
    # Add your Zoom-specific commands here
elif [[ "$choice" == "teams" ]]; then
    echo "Enabling Teams with screen placement $screen_placement"
    # Add your Teams-specific commands here
elif [[ "$choice" == "both" ]]; then
    echo "Enabling both Zoom and Teams with screen placement $screen_placement"
    # Add your commands for both here
else
    echo "Unknown choice: $choice"
    exit 1
fi