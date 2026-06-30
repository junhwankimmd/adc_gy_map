#!/usr/bin/env python3
"""Fetch each gyn-candidate ADC detail page; extract meta description (target/payload
summary) and any NCT numbers. Raw HTML is cached to disk for cheap re-runs."""
import re, json, time, html, urllib.request, urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# Prefer the full gyn list (99, incl. CT.gov-only drugs) once it exists; otherwise
# fall back to the site-tagged candidates on the very first run.
FINAL = ROOT / "data" / "gyn_final.json"
CAND = FINAL if FINAL.exists() else (ROOT / "data" / "gyn_candidates.json")
CACHE = ROOT / "data" / "detail_html"
OUT = ROOT / "data" / "gyn_details.json"
CACHE.mkdir(exist_ok=True)

UA = "Mozilla/5.0 (research; ADC gyn-oncology mapping)"
NCT_RE = re.compile(r"NCT\d{8}")
META_RE = re.compile(r'<meta name="description" content="([^"]*)"', re.I)

def fetch(url, cache_file):
    if cache_file.exists() and cache_file.stat().st_size > 1000:
        return cache_file.read_text(encoding="utf-8", errors="replace")
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                data = r.read().decode("utf-8", errors="replace")
            cache_file.write_text(data, encoding="utf-8")
            time.sleep(1.0)  # be polite
            return data
        except (urllib.error.URLError, TimeoutError) as e:
            print(f"   retry {attempt+1} for {url}: {e}")
            time.sleep(3)
    return ""

cands = json.loads(CAND.read_text())
out = []
for i, a in enumerate(cands, 1):
    cf = CACHE / f"{a['slug']}.html"
    htmltext = fetch(a["url"], cf)
    meta = META_RE.search(htmltext)
    summary = html.unescape(meta.group(1)).strip() if meta else ""
    ncts = sorted(set(NCT_RE.findall(htmltext)))
    rec = dict(a)
    rec["site_summary"] = summary
    rec["site_ncts"] = ncts
    out.append(rec)
    print(f"[{i:2d}/{len(cands)}] {a['name'][:38]:38s} NCTs={len(ncts):2d}  {'desc✓' if summary else 'desc—'}")

OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False))
tot_nct = sum(len(r["site_ncts"]) for r in out)
print(f"\nSaved {len(out)} records to {OUT.name}")
print(f"Pages with a description: {sum(bool(r['site_summary']) for r in out)}/{len(out)}")
print(f"Total NCT refs found on site: {tot_nct}")
