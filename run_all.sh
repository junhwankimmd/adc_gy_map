#!/usr/bin/env bash
# Rebuild the gynecologic-oncology ADC map end to end.
# Re-fetches the catalog, re-queries ClinicalTrials.gov + PubMed (cached), rebuilds outputs.
set -euo pipefail
cd "$(dirname "$0")"

echo "[0/6] Refreshing ADC Drug Map catalog HTML..."
curl -s -A "Mozilla/5.0 (research)" "https://www.adcreview.com/adc-drugmap/" -o data/drugmap.html

# NOTE on ordering: detail scraping (02) now covers the full gyn list (incl.
# ClinicalTrials.gov-only drugs), so it runs AFTER the gyn set is known (03+04).
python3 scripts/01_parse_drugmap.py        # catalog of all 452 ADCs + site-tag candidates
python3 scripts/03_ctgov_enrich.py         # hybrid CT.gov enrichment -> 99 gyn ADCs
python3 scripts/04_pubmed_link.py          # PubMed linkage
python3 scripts/02_scrape_details.py       # adcreview detail pages for all gyn drugs (summary/NCTs)
python3 scripts/04b_targets.py             # merge site summaries + assign target antigen
python3 scripts/05_build_dashboard.py      # interactive HTML dashboard
python3 scripts/06_export_csv.py           # flat CSV export

echo
echo "Done. Open: output/adc_gyn_dashboard.html"
echo "To force fresh API data, delete data/ctgov_cache/ and data/pubmed_cache/ first."
