#!/bin/bash

width=$1

defaults write com.t1visions.TTMenu frame -string "{{0, 0}, {$width, 2160}}"

defaults write com.t1visions.MultiTouchCalibrate frame -string "{{0, 0}, {$width, 2160}}"