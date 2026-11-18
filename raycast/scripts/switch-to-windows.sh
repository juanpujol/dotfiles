#!/bin/bash

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Switch Monitor to Windows
# @raycast.mode silent

# Optional parameters:
# @raycast.icon 🪟
# @raycast.packageName Monitor
# @raycast.description Switch the Dell U2723QE to HDMI (bento-win) via DDC/CI

# Dell U2723QE input codes: USB-C (Mac) = 27, DisplayPort = 15, HDMI = 17
/opt/homebrew/bin/m1ddc display 5DCD2644-C51B-41BA-BC1F-DCC840EC9B8C set input 17 >/dev/null && echo "Monitor on Windows"
