# Moves the Dell U2723QE to Windows (HDMI) whenever the NuPhy keyboard connects to this PC.
# Pair: kvm/mac/kvm-follow.sh does the same for the Mac (USB-C). See kvm/README.md.
# Runs as a logon task in the user's session, because DDC needs the interactive desktop.

$Keyboard = 'NuPhy Air75 V2*'   # Bluetooth channel 2, paired as "NuPhy Air75 V2-2"
$TargetInput = 17               # HDMI
$IsConnectedKey = '{83DA6326-97A6-4088-9453-A1923F573B29} 15'
$LogFile = Join-Path $env:LOCALAPPDATA 'kvm-follow.log'

Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
public static class Ddc {
  [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
  public struct PHYSICAL_MONITOR { public IntPtr hPhysicalMonitor; [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 128)] public string szPhysicalMonitorDescription; }
  delegate bool MonitorEnumProc(IntPtr hMonitor, IntPtr hdc, IntPtr rect, IntPtr data);
  [DllImport("user32.dll")] static extern bool EnumDisplayMonitors(IntPtr hdc, IntPtr clip, MonitorEnumProc cb, IntPtr data);
  [DllImport("dxva2.dll")] static extern bool GetNumberOfPhysicalMonitorsFromHMONITOR(IntPtr h, out uint n);
  [DllImport("dxva2.dll")] static extern bool GetPhysicalMonitorsFromHMONITOR(IntPtr h, uint n, [Out] PHYSICAL_MONITOR[] arr);
  [DllImport("dxva2.dll")] static extern bool SetVCPFeature(IntPtr h, byte code, uint value);
  [DllImport("dxva2.dll")] static extern bool DestroyPhysicalMonitors(uint n, PHYSICAL_MONITOR[] arr);
  public static int SetInput(uint value) {
    int ok = 0;
    EnumDisplayMonitors(IntPtr.Zero, IntPtr.Zero, (h, dc, r, d) => {
      uint n;
      if (GetNumberOfPhysicalMonitorsFromHMONITOR(h, out n) && n > 0) {
        var arr = new PHYSICAL_MONITOR[n];
        if (GetPhysicalMonitorsFromHMONITOR(h, n, arr)) {
          foreach (var m in arr) if (SetVCPFeature(m.hPhysicalMonitor, 0x60, value)) ok++;
          DestroyPhysicalMonitors(n, arr);
        }
      }
      return true;
    }, IntPtr.Zero);
    return ok;
  }
}
"@

function Log($msg) { "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $msg" | Add-Content $LogFile }

function Get-Connected {
  $dev = Get-PnpDevice -Class Bluetooth -FriendlyName $Keyboard -ErrorAction SilentlyContinue | Select-Object -First 1
  if (-not $dev) { return $false }
  (Get-PnpDeviceProperty -InstanceId $dev.InstanceId -KeyName $IsConnectedKey -ErrorAction SilentlyContinue).Data -eq $true
}

$was = Get-Connected
Log "started, keyboard connected=$was"

while ($true) {
  Start-Sleep -Seconds 1
  try {
    $now = Get-Connected
    if ($now -and -not $was) {
      $n = [Ddc]::SetInput($TargetInput)
      Log "keyboard connected, monitor -> HDMI (monitors switched: $n)"
    } elseif ($was -and -not $now) {
      Log "keyboard disconnected"
    }
    $was = $now
  } catch {
    Log "error: $($_.Exception.Message)"
  }
}
