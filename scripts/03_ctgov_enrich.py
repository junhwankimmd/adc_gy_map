#!/usr/bin/env python3
"""Hybrid ClinicalTrials.gov enrichment.

For every ADC in the catalog (not just the site-tagged gyn ones), query CT.gov by
intervention name, then POST-FILTER returned trials so that:
  - the trial's interventions actually reference the drug, and
  - at least one condition is a gynecologic malignancy.
This both validates the site's ovaries/uterus tags AND catches gyn ADCs (e.g. cervical)
that the site never tagged. PMIDs are harvested from trial references.
"""
import re, json, time, urllib.request, urllib.parse, urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ALL = ROOT / "data" / "all_adcs.json"
GYN = ROOT / "data" / "gyn_candidates.json"
OUT = ROOT / "data" / "ctgov_enriched.json"
CACHE = ROOT / "data" / "ctgov_cache"
CACHE.mkdir(exist_ok=True)

UA = "Mozilla/5.0 (research; ADC gyn-oncology mapping)"
API = "https://clinicaltrials.gov/api/v2/studies"
FIELDS = ",".join([
    "protocolSection.identificationModule.nctId",
    "protocolSection.identificationModule.briefTitle",
    "protocolSection.statusModule.overallStatus",
    "protocolSection.statusModule.startDateStruct.date",
    "protocolSection.designModule.phases",
    "protocolSection.conditionsModule.conditions",
    "protocolSection.armsInterventionsModule.interventions.name",
    "protocolSection.sponsorCollaboratorsModule.leadSponsor.name",
    "protocolSection.referencesModule.references.pmid",
    "protocolSection.referencesModule.references.type",
])

# --- gynecologic condition classifier -------------------------------------
GYN_SUBTYPES = [
    ("ovarian",     re.compile(r"ovar|fallopian|primary peritoneal|peritoneal (carcinom|high)|adnexal", re.I)),
    ("endometrial", re.compile(r"endometri|uterine|uterus|corpus uteri", re.I)),
    ("cervical",    re.compile(r"cervi", re.I)),
    ("vulvar_vaginal", re.compile(r"vulva|vagina", re.I)),
    ("gtn",         re.compile(r"trophoblast|choriocarcinoma|molar pregnan", re.I)),
    ("gyn_other",   re.compile(r"gynecolog|gynaecolog|m[uü]llerian|female (genital|reproductive)", re.I)),
]
# guard against false positives (e.g. peritoneal mesothelioma, cervical spine)
NON_GYN = re.compile(r"cervical (spine|spondyl|disc|radiculo|vertebra|myelopath)|peritoneal mesothelioma|peritoneal dialysis", re.I)

def classify_conditions(conditions):
    subs = set()
    matched = []
    for c in conditions:
        if NON_GYN.search(c):
            continue
        for name, rx in GYN_SUBTYPES:
            if rx.search(c):
                subs.add(name)
                matched.append(c)
                break
    return sorted(subs), sorted(set(matched))

def norm(s):
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()

def fetch_json(url, cache_file):
    if cache_file.exists() and cache_file.stat().st_size > 2:
        return json.loads(cache_file.read_text())
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=40) as r:
                data = json.loads(r.read().decode("utf-8", errors="replace"))
            cache_file.write_text(json.dumps(data))
            time.sleep(0.34)
            return data
        except urllib.error.HTTPError as e:
            if e.code == 404:
                cache_file.write_text("{}")
                return {}
            time.sleep(2 * (attempt + 1))
        except (urllib.error.URLError, TimeoutError) as e:
            time.sleep(2 * (attempt + 1))
    return {}

def query_drug(drug):
    """Return list of gyn trials for a drug (intervention-verified)."""
    term = drug["name"]
    url = f"{API}?{urllib.parse.urlencode({'query.intr': term, 'pageSize': 100, 'fields': FIELDS})}"
    cache_file = CACHE / (re.sub(r'[^a-z0-9]+', '_', term.lower())[:80] + ".json")
    data = fetch_json(url, cache_file)
    studies = data.get("studies", []) if isinstance(data, dict) else []

    # tokens that confirm the trial really uses THIS drug
    drug_tokens = set()
    for token in [drug["name"]] + drug.get("synonyms", []):
        nt = norm(token)
        if len(nt) >= 4:
            drug_tokens.add(nt)

    gyn_trials = []
    for s in studies:
        ps = s.get("protocolSection", {})
        ident = ps.get("identificationModule", {})
        conds = ps.get("conditionsModule", {}).get("conditions", [])
        subs, matched = classify_conditions(conds)
        if not subs:
            continue
        # verify drug is actually an intervention in this trial
        interventions = [i.get("name", "") for i in ps.get("armsInterventionsModule", {}).get("interventions", [])]
        inorm = " | ".join(norm(i) for i in interventions)
        if drug_tokens and not any(t in inorm for t in drug_tokens):
            continue
        refs = ps.get("referencesModule", {}).get("references", [])
        pmids = sorted({r["pmid"] for r in refs if r.get("pmid")})
        gyn_trials.append({
            "nct": ident.get("nctId"),
            "title": ident.get("briefTitle", ""),
            "status": ps.get("statusModule", {}).get("overallStatus", ""),
            "phases": ps.get("designModule", {}).get("phases", []),
            "start": ps.get("statusModule", {}).get("startDateStruct", {}).get("date", ""),
            "sponsor": ps.get("sponsorCollaboratorsModule", {}).get("leadSponsor", {}).get("name", ""),
            "conditions": conds,
            "gyn_conditions": matched,
            "gyn_subtypes": subs,
            "interventions": interventions,
            "pmids": pmids,
        })
    return gyn_trials

all_adcs = json.loads(ALL.read_text())
site_gyn_urls = {a["url"] for a in json.loads(GYN.read_text())}

results = []
for i, drug in enumerate(all_adcs, 1):
    trials = query_drug(drug)
    if not trials and drug["url"] not in site_gyn_urls:
        continue  # not gyn by either signal -> skip
    subtypes = sorted({s for t in trials for s in t["gyn_subtypes"]})
    pmids = sorted({p for t in trials for p in t["pmids"]})
    statuses = sorted({t["status"] for t in trials})
    phases = sorted({p for t in trials for p in t["phases"]})
    rec = {
        **{k: drug[k] for k in ("itemid", "name", "synonyms", "name_full", "company", "url", "slug", "organ_tags")},
        "site_tagged_gyn": drug["url"] in site_gyn_urls,
        "ctgov_confirmed": bool(trials),
        "gyn_subtypes": subtypes,
        "n_gyn_trials": len(trials),
        "statuses": statuses,
        "phases": phases,
        "trials": sorted(trials, key=lambda t: (t["start"] or ""), reverse=True),
        "trial_pmids": pmids,
    }
    results.append(rec)
    flag = ("S" if rec["site_tagged_gyn"] else "-") + ("C" if rec["ctgov_confirmed"] else "-")
    if i % 25 == 0 or trials:
        print(f"[{i:3d}/{len(all_adcs)}] {flag} {drug['name'][:34]:34s} trials={len(trials):2d} {','.join(subtypes)}")

results.sort(key=lambda r: (-r["n_gyn_trials"], r["name"].lower()))
OUT.write_text(json.dumps(results, indent=2, ensure_ascii=False))

both = sum(r["site_tagged_gyn"] and r["ctgov_confirmed"] for r in results)
site_only = sum(r["site_tagged_gyn"] and not r["ctgov_confirmed"] for r in results)
ct_only = sum(not r["site_tagged_gyn"] and r["ctgov_confirmed"] for r in results)
print("\n==== HYBRID SUMMARY ====")
print(f"Total gyn ADCs in dataset : {len(results)}")
print(f"  site tag AND CT.gov trial: {both}")
print(f"  site tag only (no trial) : {site_only}")
print(f"  CT.gov only (site missed): {ct_only}  <-- caught by reverse search")
from collections import Counter
sc = Counter(s for r in results for s in r["gyn_subtypes"])
print("Subtype distribution:", dict(sc))
print(f"Total gyn trials: {sum(r['n_gyn_trials'] for r in results)}")
print(f"Drugs with trial PMIDs: {sum(bool(r['trial_pmids']) for r in results)}")
