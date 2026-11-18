#!/bin/bash
# Moves the Dell U2723QE to the Mac (USB-C) whenever the NuPhy keyboard connects to the Mac.
# Pair: kvm/windows/kvm-follow.ps1 does the same for Windows (HDMI). See kvm/README.md.

KEYBOARD="NuPhy Air75 V2"                          # Bluetooth channel 1 (BLE HID product name)
DISPLAY_ID="5DCD2644-C51B-41BA-BC1F-DCC840EC9B8C"  # DELL U2723QE
INPUT=27                                           # USB-C

M1DDC=/opt/homebrew/bin/m1ddc

log() { echo "$(date '+%F %T') $*"; }

# The BLE HID device only exists in the IORegistry while the keyboard is connected.
# blueutil --is-connected misreports BLE keyboards, so it is not used here.
connected() {
  if /usr/sbin/ioreg -r -c IOHIDUserDevice -k Product | grep -q "\"Product\" = \"$KEYBOARD\""; then
    echo 1
  else
    echo 0
  fi
}

was=$(connected)
log "started, keyboard connected=$was"

while true; do
  sleep 1
  now=$(connected)
  if [ "$now" = 1 ] && [ "$was" = 0 ]; then
    if "$M1DDC" display "$DISPLAY_ID" set input "$INPUT" >/dev/null; then
      log "keyboard connected, monitor -> USB-C"
    else
      log "keyboard connected, monitor switch failed"
    fi
  elif [ "$now" = 0 ] && [ "$was" = 1 ]; then
    log "keyboard disconnected"
  fi
  was=$now
done
