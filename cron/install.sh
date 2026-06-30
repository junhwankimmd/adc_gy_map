#!/usr/bin/env bash
# Install a macOS LaunchAgent that rebuilds the ADC gyn map on a schedule.
# Default: DAILY at 07:00. Set WEEKDAY (0-6, 0=Sun) for a weekly schedule instead.
# Override the time with HOUR (0-23) and MINUTE (0-59).
set -euo pipefail

PROJ="$(cd "$(dirname "$0")/.." && pwd)"
LABEL="com.adcgynmap.refresh"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
HOUR="${HOUR:-7}"
MINUTE="${MINUTE:-0}"
WEEKDAY="${WEEKDAY:-}"    # empty = daily; set 0-6 for weekly (1 = Monday)
PYTHON="$(command -v python3 || echo /usr/bin/python3)"
PYDIR="$(dirname "$PYTHON")"

# Build the StartCalendarInterval dict: include <Weekday> only for a weekly schedule.
if [ -n "$WEEKDAY" ]; then
  CAL="<key>Weekday</key><integer>$WEEKDAY</integer><key>Hour</key><integer>$HOUR</integer><key>Minute</key><integer>$MINUTE</integer>"
  SCHED_DESC="weekly (weekday=$WEEKDAY) at $HOUR:$(printf '%02d' "$MINUTE")"
else
  CAL="<key>Hour</key><integer>$HOUR</integer><key>Minute</key><integer>$MINUTE</integer>"
  SCHED_DESC="daily at $HOUR:$(printf '%02d' "$MINUTE")"
fi

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
    <string>$PROJ/cron/daily_update.sh</string>
  </array>
  <key>WorkingDirectory</key><string>$PROJ</string>
  <key>EnvironmentVariables</key>
  <dict>
    <key>PATH</key><string>$PYDIR:/usr/bin:/bin:/usr/sbin:/sbin:/usr/local/bin:/opt/homebrew/bin</string>
  </dict>
  <key>StartCalendarInterval</key>
  <dict>$CAL</dict>
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
echo "Schedule: $SCHED_DESC"
echo "Action:   rebuild dataset + dashboard, then git commit/push (updates GitHub Pages)"
echo "Logs:     $PROJ/logs/refresh.{out,err}.log"
echo "Run now to test:  launchctl start $LABEL"
echo "Uninstall:        $PROJ/cron/uninstall.sh"
