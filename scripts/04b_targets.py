#!/usr/bin/env python3
"""Derive the target antigen for each gyn ADC (offline, no network).

Strategy: (1) alias regex search over name_full + site_summary; (2) if nothing,
fall back to a curated antibody-INN-stem -> target map. Result -> `target` field
written back into data/gyn_final.json.
"""
import re, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "gyn_final.json"
DETAILS = ROOT / "data" / "gyn_details.json"

# canonical target -> list of regex alias patterns (searched case-insensitively)
ALIASES = [
    ("HER2",          [r"her[\s-]?2\b", r"erbb[\s-]?2", r"\bcd340\b"]),
    ("HER3",          [r"her[\s-]?3\b", r"erbb[\s-]?3"]),
    ("TROP2",         [r"trop[\s-]?2\b", r"tacstd2"]),
    ("FRα (FOLR1)",   [r"folr1", r"folate receptor", r"fr[\s-]?alpha", r"fr[\s-]?α", r"frα"]),
    ("B7-H4",         [r"b7[\s-]?h4", r"vtcn1"]),
    ("B7-H3",         [r"b7[\s-]?h3", r"\bcd276\b"]),
    ("CDH6",          [r"\bcdh6\b", r"cadherin[\s-]?6"]),
    ("MSLN",          [r"mesothelin", r"\bmsln\b"]),
    ("NaPi2b",        [r"napi[\s-]?2b", r"slc34a2"]),
    ("MUC16",         [r"muc[\s-]?16", r"\bca[\s-]?125\b"]),
    ("CEACAM5",       [r"ceacam[\s-]?5", r"\bceacam\b", r"\bcea\b(?!cam)"]),
    ("Nectin-4",      [r"nectin[\s-]?4"]),
    ("Tissue Factor", [r"tissue factor", r"\btf[\s-]?011", r"coagulation factor", r"anti[\s-]?tf\b"]),
    ("CD25 (IL2RA)",  [r"il2ra", r"interleukin[\s-]?2 receptor", r"\bcd25\b"]),
    ("HSP90",         [r"heat shock protein 90", r"\bhsp90\b"]),
    ("PD-L1",         [r"pd-?l1", r"pd-?\(l\)1", r"\bcd274\b"]),
    ("CAIX",          [r"carbonic anhydrase ix", r"\bcaix\b", r"\bca9\b", r"\bg250\b"]),
    ("EphA2",         [r"epha2", r"eph receptor a2", r"ephrin[\s-]?receptor a2"]),
    ("TAG-72",        [r"tag-?72"]),
    ("DLL3",          [r"\bdll[\s-]?3\b"]),
    ("CD70",          [r"\bcd70\b"]),
    ("AXL",           [r"\baxl\b"]),
    ("cMET",          [r"c[\s-]?met\b", r"\bmet\b proto", r"hepatocyte growth factor receptor"]),
    ("EGFR",          [r"\begfr\b"]),
    ("LIV-1",         [r"liv[\s-]?1\b", r"slc39a6"]),
    ("5T4",           [r"\b5t4\b", r"\btpbg\b", r"trophoblast glycoprotein"]),
    ("PTK7",          [r"\bptk7\b"]),
    ("ROR1",          [r"\bror1\b"]),
    ("ROR2",          [r"\bror2\b"]),
    ("CLDN6",         [r"claudin[\s-]?6\b", r"\bcldn6\b"]),
    ("CLDN18.2",      [r"claudin[\s-]?18", r"\bcldn18"]),
    ("GPNMB",         [r"\bgpnmb\b"]),
    ("ENPP3",         [r"\benpp3\b"]),
    ("SLITRK6",       [r"slitrk6"]),
    ("Ly6E",          [r"\bly6e\b"]),
    ("EFNA4",         [r"\befna4\b", r"ephrin[\s-]?a4"]),
    ("ADAM9",         [r"\badam9\b"]),
    ("gpA33",         [r"\bgpa33\b", r"\ba33\b"]),
    ("STEAP1",        [r"\bsteap1\b"]),
    ("GUCY2C",        [r"\bgucy2c\b"]),
    ("DPEP3",         [r"\bdpep3\b"]),
    ("Mucin-1",       [r"\bmuc1\b(?!6)", r"mucin[\s-]?1\b"]),
    ("PSMA",          [r"\bpsma\b", r"folh1"]),
    ("Integrin",      [r"integrin", r"\bav?b6\b"]),
    # hematologic (rare here but for completeness)
    ("CD19",          [r"\bcd19\b"]),
    ("CD22",          [r"\bcd22\b"]),
    ("CD30",          [r"\bcd30\b"]),
    ("CD33",          [r"\bcd33\b"]),
    ("CD37",          [r"\bcd37\b"]),
    ("CD79b",         [r"\bcd79b\b"]),
    ("CD123",         [r"\bcd123\b"]),
    ("BCMA",          [r"\bbcma\b", r"\btnfrsf17\b"]),
]

# antibody INN stem -> target (fallback when text has no antigen keyword)
INN_STEM = {
    "trastuzumab": "HER2", "pertuzumab": "HER2", "disitamab": "HER2", "hertuzumab": "HER2",
    "zanidatamab": "HER2", "zenocutuzumab": "HER2",
    "sacituzumab": "TROP2", "datopotamab": "TROP2",
    "mirvetuximab": "FRα (FOLR1)", "farletuzumab": "FRα (FOLR1)", "luveltamab": "FRα (FOLR1)",
    "rinatabart": "FRα (FOLR1)",
    "tisotumab": "Tissue Factor",
    "enfortumab": "Nectin-4",
    "patritumab": "HER3", "lonigutamab": "HER3",
    "anetumab": "MSLN",
    "upifitamab": "NaPi2b", "lifastuzumab": "NaPi2b",
    "sofituzumab": "MUC16",
    "raludotatug": "CDH6",
    "ifinatamab": "B7-H3", "vobramitamab": "B7-H3", "mipasetamab": "B7-H3",
    "telisotuzumab": "cMET",
    "cofetuzumab": "PTK7",
    "ladiratuzumab": "LIV-1",
    "glembatumumab": "GPNMB",
    "depatuxizumab": "EGFR", "losatuxizumab": "EGFR",
    "coltuximab": "CD19", "denintuzumab": "CD19", "loncastuximab": "CD19",
    "inotuzumab": "CD22", "epratuzumab": "CD22",
    "gemtuzumab": "CD33", "vadastuximab": "CD33",
    "brentuximab": "CD30",
    "belantamab": "BCMA",
    "polatuzumab": "CD79b", "iladatuzumab": "CD79b",
    "naratuximab": "CD37",
    "indatuximab": "CD138",
    "tusamitamab": "CEACAM5", "labetuzumab": "CEACAM5",
    "praluzatamab": "ALCAM (CD166)",
    "cantuzumab": "CanAg (MUC1)", "bivatuzumab": "CD44v6",
    "indusatumab": "GUCY2C", "tabituximab": "PD-L1",
    "samrotamab": "LRRC15", "lorvotuzumab": "CD56",
    "pivekimab": "CD123",
    "rovalpituzumab": "DLL3",
    "tamrintamab": "DPEP3",
    "izalontamab": "EGFR × HER3",
}

# Curated code-name -> target for well-established ADCs whose adcreview page
# carries no antigen text (publicly disclosed targets).
CODE_MAP = {
    "bat8006": "FRα (FOLR1)",
    "torl-1-23": "CLDN6",
    "mgc026": "B7-H3",
    "cusp06": "CDH6",
    "adrx-0706": "Nectin-4",
    "tub-040": "NaPi2b",
    "cdx-014": "TIM-1",
    "sgn-15": "Lewis Y",
}

# ---- payload (cytotoxic warhead) classifier ----
# Ordered: specific patterns first, generic last.
PAYLOAD_ALIASES = [
    ("MMAE (auristatin)",   [r"\bmmae\b", r"monomethyl auristatin e", r"vc[\s-]?mmae", r"mc[\s-]?vc[\s-]?pabc[\s-]?mmae"]),
    ("MMAF (auristatin)",   [r"\bmmaf\b", r"monomethyl auristatin f"]),
    ("DXd (Topo-I)",        [r"\bdxd\b", r"deruxtecan", r"exatecan deriv"]),
    ("SN-38 (Topo-I)",      [r"\bsn[\s-]?38\b"]),
    ("Topoisomerase-I inhibitor", [r"topoisomerase", r"camptothecin", r"\bexatecan\b", r"belotecan", r"topo[\s-]?i\b", r"topo[\s-]?1\b"]),
    ("Maytansinoid (DM1)",  [r"\bdm[\s-]?1\b", r"emtansine", r"mertansine"]),
    ("Maytansinoid (DM4)",  [r"\bdm[\s-]?4\b", r"ravtansine", r"soravtansine"]),
    ("Maytansinoid",        [r"maytansin"]),
    ("Calicheamicin",       [r"calicheamicin", r"ozogamicin"]),
    ("PBD dimer",           [r"pyrrolobenzodiazepine", r"\bpbd\b", r"sg3199", r"tesirine", r"talirine"]),
    ("Duocarmycin",         [r"duocarmaz", r"duocarmycin", r"seco[\s-]?duba"]),
    ("Eribulin",            [r"eribulin"]),
    ("Tubulysin",           [r"tubulysin"]),
    ("Amanitin",            [r"amanitin", r"amatoxin"]),
    ("Auristatin",          [r"auristatin", r"\bav?e\b dolastatin", r"dolastatin"]),
]
PAYLOAD_STEM = [  # antibody-INN payload sub-stem -> payload (checked as substring, order matters)
    ("vedotin", "MMAE (auristatin)"), ("mafodotin", "MMAF (auristatin)"),
    ("deruxtecan", "DXd (Topo-I)"), ("govitecan", "SN-38 (Topo-I)"),
    ("emtansine", "Maytansinoid (DM1)"), ("mertansine", "Maytansinoid (DM1)"),
    ("ravtansine", "Maytansinoid (DM4)"), ("soravtansine", "Maytansinoid (DM4)"),
    ("ozogamicin", "Calicheamicin"),
    ("tesirine", "PBD dimer"), ("talirine", "PBD dimer"),
    ("duocarmazine", "Duocarmycin"), ("ecteribulin", "Eribulin"),
    ("tansine", "Maytansinoid"),
    ("tecan", "Topoisomerase-I inhibitor"),   # rezetecan/tirumotecan/sesutecan/samrotecan/...
    ("dotin", "Auristatin"),                  # any remaining ...dotin
]

def find_payload(rec):
    hay = (rec.get("name_full", "") + " || " + rec.get("site_summary", "")).lower()
    for canon, pats in PAYLOAD_ALIASES:
        for p in pats:
            if re.search(p, hay):
                return canon
    name_l = rec.get("name_full", "").lower()
    for stem, pay in PAYLOAD_STEM:
        if stem in name_l:
            return pay
    return "Other / unspecified"

def find_target(rec):
    hay = (rec.get("name_full", "") + " || " + rec.get("site_summary", "")).lower()
    for canon, pats in ALIASES:
        for p in pats:
            if re.search(p, hay):
                return canon
    # INN stem fallback
    name_l = (rec.get("name_full", "")).lower()
    for stem, tgt in INN_STEM.items():
        if stem in name_l:
            return tgt
    # curated code-name fallback
    for code, tgt in CODE_MAP.items():
        if code in name_l or code in (rec.get("slug", "")):
            return tgt
    return "Other / unspecified"

data = json.loads(SRC.read_text())

# Merge site_summary / site_ncts from the detail scrape (step 02), which step 03
# dropped. Keyed by URL. Only the site-tagged candidates have details.
details = {d["url"]: d for d in json.loads(DETAILS.read_text())} if DETAILS.exists() else {}
n_merged = 0
for rec in data:
    det = details.get(rec["url"])
    if det:
        if det.get("site_summary"):
            rec["site_summary"] = det["site_summary"]
            n_merged += 1
        rec["site_ncts"] = det.get("site_ncts", [])
    rec.setdefault("site_summary", "")
print(f"Merged site descriptions into {n_merged} drugs.")

from collections import Counter
c, cp = Counter(), Counter()
for rec in data:
    rec["target"] = find_target(rec)
    rec["payload"] = find_payload(rec)
    c[rec["target"]] += 1
    cp[rec["payload"]] += 1
SRC.write_text(json.dumps(data, indent=2, ensure_ascii=False))

print(f"Assigned target + payload to {len(data)} drugs.")
print("\nTarget distribution:")
for t, n in c.most_common():
    print(f"  {n:3d}  {t}")
print("\nPayload distribution:")
for t, n in cp.most_common():
    print(f"  {n:3d}  {t}")
unk = [r["name"] for r in data if r["target"] == "Other / unspecified"]
unkp = [r["name"] for r in data if r["payload"] == "Other / unspecified"]
print(f"\nTarget unresolved ({len(unk)}); Payload unresolved ({len(unkp)})")
