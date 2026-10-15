# Registers Notification Piper to start silently at logon (current user).
$dir = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonw = Join-Path $dir ".venv\Scripts\pythonw.exe"
$script = Join-Path $dir "notification_piper.py"

$action = New-ScheduledTaskAction -Execute $pythonw -Argument "`"$script`"" -WorkingDirectory $dir
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit 0
Register-ScheduledTask -TaskName "NotificationPiper" -Action $action -Trigger $trigger -Settings $settings -Force | Out-Null
Start-ScheduledTask -TaskName "NotificationPiper"
Write-Host "Installed and started. Remove with: Unregister-ScheduledTask -TaskName NotificationPiper"
