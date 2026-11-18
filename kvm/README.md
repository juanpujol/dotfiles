# kvm

Software KVM for the Mac and bento-win sharing one Dell U2723QE. The keyboard picks the computer, and the monitor
follows it.

- NuPhy Air75 V2: `Fn + 1` = Mac (Bluetooth channel 1), `Fn + 2` = Windows (Bluetooth channel 2)
- Whichever computer the keyboard connects to switches the monitor input to itself over DDC/CI
- Dell U2723QE inputs: USB-C (Mac) = 27, DisplayPort = 15, HDMI (bento-win) = 17

The two sides are independent and never talk to each other.

## Mac

`mac/kvm-follow.sh`, run by the launchd agent `mac/dev.juan.kvm-follow.plist`. It polls the IORegistry for the
keyboard's BLE HID device (`blueutil --is-connected` misreports BLE keyboards) and runs `m1ddc` on connect.

```sh
brew install m1ddc
cp ~/dotfiles/kvm/mac/dev.juan.kvm-follow.plist ~/Library/LaunchAgents/
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/dev.juan.kvm-follow.plist
```

Log: `~/Library/Logs/kvm-follow.log`. Restart after editing: `launchctl kickstart -k gui/$(id -u)/dev.juan.kvm-follow`

## Windows

`windows/kvm-follow.ps1`, installed at `%USERPROFILE%\kvm\kvm-follow.ps1` and run by the scheduled task `kvm-follow`
(at logon, in the user's session, headless). It polls the Bluetooth device's `IsConnected` property and sets the
input through `dxva2.dll`, so nothing extra needs installing. DDC only works from the interactive session, not from
SSH or a service.

Update over SSH:

```sh
scp ~/dotfiles/kvm/windows/kvm-follow.ps1 jp@192.168.68.52:kvm/kvm-follow.ps1
ssh jp@192.168.68.52 'schtasks /End /TN kvm-follow & schtasks /Run /TN kvm-follow'
```

Log: `%LOCALAPPDATA%\kvm-follow.log`. Windows needs sleep disabled on AC power, or the watcher stops with the PC.
