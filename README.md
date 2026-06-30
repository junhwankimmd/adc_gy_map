# Gynecologic-Oncology ADC Map

Filters the [ADC Review Drug Map](https://www.adcreview.com/adc-drugmap/) down to antibody-drug
conjugates relevant to **gynecologic cancers** (ovarian/fallopian/peritoneal, endometrial/uterine,
cervical, vulvar/vaginal, GTN) and links each drug to its **ClinicalTrials.gov** trials and
**PubMed** literature.

## Output

- **`output/adc_gyn_dashboard.html`** — self-contained interactive dashboard (open in any browser):
  - Filter by **gyn subtype / target antigen / source / trial status / phase**, full-text search.
  - **Summary panel** (▸ Summary): live counts by target / phase / company / subtype; click any row to filter.
  - **한국어 / English toggle** (top-right): translates the UI; drug names, company names and
    trial/paper titles stay in their original form.
  - Click a drug to drill into its trials (→ ClinicalTrials.gov) and papers (→ PubMed).
- **`output/adc_gyn_table.csv`** — flat one-row-per-drug table (incl. `target`).
- **`data/gyn_final.json`** — full structured dataset.

## Method (hybrid filtering)

The site's on-page filter is a client-side keyword filter with only two gyn organ tags
(`ovaries`, `uterus`) — **no cervix tag**, and "ovaries" reflects target *expression*, not active
gyn-cancer development. So site tags alone are imprecise. Instead:

1. **Catalog** — parse all 452 ADCs from the drugmap page (`data-terms` / `<li>` attributes).
2. **Site first-pass** — flag the ~69 drugs tagged `ovaries`/`uterus`.
3. **ClinicalTrials.gov hybrid** — query CT.gov API v2 by intervention for *every* ADC, then keep
   only trials whose **conditions** match a gynecologic malignancy AND whose **interventions**
   actually reference the drug. This validates the site tags and **catches gyn ADCs the site never
   tagged** (e.g. cervical — including FDA-approved **tisotumab vedotin**).
4. **PubMed** — papers from each trial's references + a phrase-matched PubMed search
   (drug `[tiab]` AND gyn terms); generic/ambiguous drug names are skipped to avoid review-article noise.

### Source labels in the dashboard
- **Tag + Trial** — site-tagged *and* has a real gyn trial (highest confidence).
- **Tag only** — site-tagged but no active gyn trial found (catalog/legacy or non-clinical).
- **CT.gov only** — *not* on the site's gyn tags but has a gyn trial (reverse-search catch).

## Current snapshot (built 2026-06-30)

99 gyn ADCs · 119 gyn trials · 235 PubMed papers
Subtypes: ovarian 42, endometrial 27, cervical 17, vulvar/vaginal 2, gyn-other 3
Source mix: Tag+Trial 22, Tag-only 47, CT.gov-only 30

## Rebuild

```bash
./run_all.sh          # refetch + re-run all steps (API calls are cached under data/*_cache/)
```

Delete `data/ctgov_cache/` and `data/pubmed_cache/` to force fresh API data.

## Scheduled auto-refresh (macOS launchd)

```bash
bash cron/install.sh            # weekly, Monday 07:00 (default)
WEEKDAY=3 HOUR=6 bash cron/install.sh   # e.g. Wednesday 06:00
launchctl start com.adcgynmap.refresh   # run once now to test
bash cron/uninstall.sh          # remove
```

Logs go to `logs/refresh.{out,err}.log`. The agent runs `run_all.sh`, which refetches the
catalog and rebuilds all outputs (API responses stay cached, so only new/changed records hit
the network).

## Caveats
- CT.gov intervention search + condition post-filter is high-precision but not exhaustive; rare
  basket trials labelled only "advanced solid tumors" without a gyn condition are not counted.
- "Tag only" drugs are mostly discontinued or early/non-clinical — kept for completeness, flagged.
- Not medical advice. Verify trial status and eligibility on ClinicalTrials.gov before any use.

## Data sources
adcreview.com ADC Drug Map · ClinicalTrials.gov API v2 · NCBI PubMed E-utilities.
