#!/usr/bin/env python3
"""PubMed linkage via NCBI E-utilities.

Two sources of papers per gyn ADC:
  (1) PMIDs already attached to its ClinicalTrials.gov trials (referencesModule)
  (2) a targeted PubMed search: drug name/synonyms AND gynecologic-cancer terms
Then esummary fetches title/journal/year/authors for every unique PMID.
"""
import json, time, re, urllib.request, urllib.parse, urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "ctgov_enriched.json"
OUT = ROOT / "data" / "gyn_final.json"
CACHE = ROOT / "data" / "pubmed_cache"
CACHE.mkdir(exist_ok=True)

UA = "Mozilla/5.0 (research; ADC gyn-oncology mapping; mailto:junhwankimmd@gmail.com)"
EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
GYN_QUERY = ('(ovarian OR fallopian OR peritoneal OR endometrial OR uterine OR '
             'cervical OR vulvar OR vaginal OR gynecologic OR gynaecologic)')

def get(url, cache_key):
    cf = CACHE / (re.sub(r"[^a-z0-9]+", "_", cache_key.lower())[:90] + ".json")
    if cf.exists() and cf.stat().st_size > 2:
        return json.loads(cf.read_text())
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=40) as r:
                data = json.loads(r.read().decode("utf-8", errors="replace"))
            cf.write_text(json.dumps(data))
            time.sleep(0.4)  # <3 req/s without API key
            return data
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
            time.sleep(2 * (attempt + 1))
    return {}

GENERIC = {"adc", "drug", "conjugate", "antibody", "anti", "the", "a", "an",
           "her", "her2", "her3", "vedotin", "deruxtecan"}

def is_specific(cand):
    """A drug name/synonym is specific enough to search PubMed if, after removing
    generic ADC words, a distinctive token (len>=4, or len>=4 with a digit) remains."""
    words = re.findall(r"[a-z0-9]+", cand.lower())
    core = [w for w in words if w not in GENERIC]
    return any(len(w) >= 4 for w in core)

def esearch(drug):
    cands = [drug["name"]] + drug.get("synonyms", [])
    cands = [c.strip() for c in cands if is_specific(c)][:4]
    if not cands:
        return []  # no distinctive identifier -> skip search (avoid generic-review noise)
    # exact phrase match in title/abstract keeps results specific to THIS ADC
    drugq = " OR ".join(f'"{c}"[tiab]' for c in cands)
    term = f"({drugq}) AND {GYN_QUERY}"
    url = f"{EUTILS}/esearch.fcgi?" + urllib.parse.urlencode(
        {"db": "pubmed", "term": term, "retmode": "json", "retmax": 20, "sort": "relevance"})
    d = get(url, "search2_" + drug["slug"])
    return d.get("esearchresult", {}).get("idlist", [])

def esummary(pmids):
    out = {}
    for i in range(0, len(pmids), 150):
        chunk = pmids[i:i+150]
        url = f"{EUTILS}/esummary.fcgi?" + urllib.parse.urlencode(
            {"db": "pubmed", "id": ",".join(chunk), "retmode": "json"})
        d = get(url, "sum_" + "_".join(chunk[:1]) + f"_{i}")
        res = d.get("result", {})
        for pid in res.get("uids", []):
            r = res[pid]
            authors = [a["name"] for a in r.get("authors", []) if a.get("authtype") == "Author"]
            out[pid] = {
                "pmid": pid,
                "title": r.get("title", "").rstrip("."),
                "journal": r.get("source", ""),
                "year": (r.get("pubdate", "")[:4]),
                "first_author": authors[0] if authors else "",
                "n_authors": len(authors),
                "doi": next((a["value"] for a in r.get("articleids", []) if a.get("idtype") == "doi"), ""),
            }
    return out

drugs = json.loads(SRC.read_text())
all_pmids = set()
for d in drugs:
    search_pmids = esearch(d)
    d["search_pmids"] = search_pmids
    d["pmids"] = sorted(set(d.get("trial_pmids", [])) | set(search_pmids), key=int)
    all_pmids |= set(d["pmids"])
    print(f"  {d['name'][:36]:36s} trial={len(d.get('trial_pmids',[])):2d} search={len(search_pmids):2d} total={len(d['pmids']):2d}")

print(f"\nFetching metadata for {len(all_pmids)} unique PMIDs...")
meta = esummary(sorted(all_pmids, key=int))

for d in drugs:
    papers = [meta[p] for p in d["pmids"] if p in meta]
    for pp in papers:
        pp = pp  # tag source
    # tag whether each came from a trial ref
    tset = set(d.get("trial_pmids", []))
    for pp in papers:
        pp["from_trial"] = pp["pmid"] in tset
    d["papers"] = sorted(papers, key=lambda x: (x["year"] or "0"), reverse=True)

OUT.write_text(json.dumps(drugs, indent=2, ensure_ascii=False))
print(f"\nSaved {OUT.name}")
print(f"Total unique papers: {len(meta)}")
print(f"Drugs with >=1 paper: {sum(bool(d['papers']) for d in drugs)}/{len(drugs)}")
