param(
  [string]$Title = "Claude Code",
  [string]$Body  = "Task finished - ready for input"
)
$ErrorActionPreference = 'Stop'

# Always play an audible cue first (independent of the visual path).
try { [System.Media.SystemSounds]::Asterisk.Play() } catch {}

try {
  # Preferred: native WinRT toast -> lands in Action Center, shows even when the
  # terminal is unfocused or closed, carries the system's default notification sound.
  [void][Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime]
  [void][Windows.UI.Notifications.ToastNotification, Windows.UI.Notifications, ContentType = WindowsRuntime]
  [void][Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime]

  $AppId = '{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\WindowsPowerShell\v1.0\powershell.exe'
  $tmpl  = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02)
  $t     = $tmpl.GetElementsByTagName('text')
  [void]$t.Item(0).AppendChild($tmpl.CreateTextNode($Title))
  [void]$t.Item(1).AppendChild($tmpl.CreateTextNode($Body))

  $toast = [Windows.UI.Notifications.ToastNotification]::new($tmpl)
  [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier($AppId).Show($toast)
}
catch {
  # Fallback: tray balloon (no dependencies). Keep the process alive briefly so it renders.
  Add-Type -AssemblyName System.Windows.Forms, System.Drawing
  $n = New-Object System.Windows.Forms.NotifyIcon
  $n.Icon = [System.Drawing.SystemIcons]::Information
  $n.Visible = $true
  $n.ShowBalloonTip(6000, $Title, $Body, [System.Windows.Forms.ToolTipIcon]::Info)
  Start-Sleep -Seconds 6
  $n.Dispose()
}
