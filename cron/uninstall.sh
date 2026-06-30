#!/usr/bin/env bash
# Remove the ADC gyn map auto-refresh LaunchAgent.
set -euo pipefail
LABEL="com.adcgynmap.refresh"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
launchctl unload "$PLIST" 2>/dev/null || true
rm -f "$PLIST"
echo "Removed $PLIST"
