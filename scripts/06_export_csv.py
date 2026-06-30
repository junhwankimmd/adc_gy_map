#!/usr/bin/env python3
"""Flat CSV export of the gyn ADC dataset (one row per drug)."""
import json, csv
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
d = json.loads((ROOT / "data" / "gyn_final.json").read_text())
out = ROOT / "output" / "adc_gyn_table.csv"
cols = ["name", "synonyms", "company", "target", "payload", "gyn_subtypes", "site_tagged_gyn",
        "ctgov_confirmed", "n_gyn_trials", "phases", "statuses", "n_papers",
        "site_summary", "ncts", "pmids", "url"]
with out.open("w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(cols)
    for x in d:
        w.writerow([
            x["name"], " | ".join(x.get("synonyms", [])), x["company"], x.get("target", ""), x.get("payload", ""),
            ", ".join(x["gyn_subtypes"]), x["site_tagged_gyn"], x["ctgov_confirmed"],
            x["n_gyn_trials"], ", ".join(x.get("phases", [])), ", ".join(x.get("statuses", [])),
            len(x.get("papers", [])), x.get("site_summary", ""),
            "; ".join(t["nct"] for t in x.get("trials", [])),
            "; ".join(p["pmid"] for p in x.get("papers", [])), x["url"],
        ])
print("Wrote", out, "rows:", len(d))
