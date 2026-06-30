#!/usr/bin/env bash
# Install a macOS LaunchAgent that rebuilds the ADC gyn map on a schedule.
# Default: weekly, Monday 07:00. Override with WEEKDAY (0-6, 0=Sun) and HOUR.
set -euo pipefail

PROJ="$(cd "$(dirname "$0")/.." && pwd)"
LABEL="com.adcgynmap.refresh"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
WEEKDAY="${WEEKDAY:-1}"   # 1 = Monday
HOUR="${HOUR:-7}"
PYTHON="$(command -v python3 || echo /usr/bin/python3)"
PYDIR="$(dirname "$PYTHON")"

mkdir -p "$PROJ/logs" "$HOME/Library/LaunchAgents"

cat > "$PLIST" <<PLISTEOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>$PROJ/run_all.sh</string>
  </array>
  <key>WorkingDirectory</key><string>$PROJ</string>
  <key>EnvironmentVariables</key>
  <dict>
    <key>PATH</key><string>$PYDIR:/usr/bin:/bin:/usr/sbin:/sbin:/usr/local/bin:/opt/homebrew/bin</string>
  </dict>
  <key>StartCalendarInterval</key>
  <dict>
    <key>Weekday</key><integer>$WEEKDAY</integer>
    <key>Hour</key><integer>$HOUR</integer>
    <key>Minute</key><integer>0</integer>
  </dict>
  <key>RunAtLoad</key><false/>
  <key>StandardOutPath</key><string>$PROJ/logs/refresh.out.log</string>
  <key>StandardErrorPath</key><string>$PROJ/logs/refresh.err.log</string>
</dict>
</plist>
PLISTEOF

# reload
launchctl unload "$PLIST" 2>/dev/null || true
launchctl load "$PLIST"
echo "Installed LaunchAgent: $PLIST"
echo "Schedule: weekday=$WEEKDAY hour=$HOUR:00 (weekly)"
echo "Logs: $PROJ/logs/refresh.{out,err}.log"
echo "Run now to test:  launchctl start $LABEL"
echo "Uninstall:        $PROJ/cron/uninstall.sh"
