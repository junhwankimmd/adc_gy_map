#!/usr/bin/env bash
# Daily job: rebuild the ADC gyn map, then commit & push so the public
# GitHub Pages dashboard (https://junhwankimmd.github.io/adc_gy_map/) stays current.
# Invoked by the launchd agent installed via cron/install.sh.
set -uo pipefail
cd "$(dirname "$0")/.."

echo "===== $(date '+%Y-%m-%d %H:%M:%S') daily update start ====="

# 1) Rebuild everything (refetch catalog + cached API calls + regenerate outputs).
if ! bash run_all.sh; then
  echo "run_all.sh failed; aborting push." >&2
  exit 1
fi

# 2) Commit & push only if something changed and this is a git repo with a remote.
if [ -d .git ] && git remote get-url origin >/dev/null 2>&1; then
  git add -A data/*.json output/ docs/ 2>/dev/null || true
  if git diff --cached --quiet; then
    echo "No changes to publish."
  else
    git commit -q -m "Daily refresh: $(date '+%Y-%m-%d')" \
      -m "Automated rebuild of dataset + dashboard (launchd)."
    if git push -q origin HEAD; then
      echo "Pushed. GitHub Pages will rebuild shortly."
    else
      echo "git push failed (check credentials: gh auth status / gh auth setup-git)." >&2
    fi
  fi
else
  echo "Not a git repo with an 'origin' remote; skipping push."
fi

echo "===== $(date '+%Y-%m-%d %H:%M:%S') daily update done ====="
