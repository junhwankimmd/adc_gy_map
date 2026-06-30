#!/usr/bin/env python3
"""Parse the ADC Review drugmap HTML into a structured table of all ADCs."""
import re, json, html, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "drugmap.html"
OUT_ALL = ROOT / "data" / "all_adcs.json"
OUT_GYN = ROOT / "data" / "gyn_candidates.json"

# Gyn organ tags actually used by the site
GYN_ORGAN_TAGS = {"ovaries", "uterus"}

raw = SRC.read_text(encoding="utf-8", errors="replace")

# Each entry: <li itemscope="..." itemid="..." data-terms="..."> <a href="URL">NAME<span>COMPANY</span></a></li>
li_re = re.compile(
    r'<li\s+itemscope="(?P<organs>[^"]*)"\s+itemid="(?P<itemid>\d+)"\s+data-terms="(?P<terms>[^"]*)">\s*'
    r'<a\s+href="(?P<url>[^"]+)">(?:<!--.*?-->)?\s*(?P<name>.*?)<span>(?P<company>.*?)</span>\s*</a>\s*</li>',
    re.S,
)

def clean(s):
    s = re.sub(r"<[^>]+>", " ", s or "")
    s = html.unescape(s)
    return re.sub(r"\s+", " ", s).strip()

adcs = []
for m in li_re.finditer(raw):
    organs = [o for o in m.group("organs").split() if o]
    url = html.unescape(m.group("url").strip())
    slug = url.rstrip("/").rsplit("/", 1)[-1]
    name_full = clean(m.group("name"))
    # split synonyms on the pipe used by the site
    names = [n.strip() for n in name_full.split("|") if n.strip()]
    adcs.append({
        "itemid": m.group("itemid"),
        "name": names[0] if names else name_full,
        "synonyms": names[1:],
        "name_full": name_full,
        "company": clean(m.group("company")),
        "url": url,
        "slug": slug,
        "organ_tags": organs,
    })

# de-dup by url (some entries repeat)
seen, uniq = set(), []
for a in adcs:
    if a["url"] in seen:
        continue
    seen.add(a["url"])
    uniq.append(a)
adcs = uniq

OUT_ALL.write_text(json.dumps(adcs, indent=2, ensure_ascii=False))

gyn = [a for a in adcs if GYN_ORGAN_TAGS & set(a["organ_tags"])]
for a in gyn:
    tags = set(a["organ_tags"])
    a["gyn_site_tags"] = sorted(GYN_ORGAN_TAGS & tags)
OUT_GYN.write_text(json.dumps(gyn, indent=2, ensure_ascii=False))

print(f"Total ADC entries parsed (deduped): {len(adcs)}")
print(f"Gyn candidates (ovaries/uterus tag): {len(gyn)}")
print(f"  - ovaries: {sum('ovaries' in a['organ_tags'] for a in adcs)}")
print(f"  - uterus : {sum('uterus' in a['organ_tags'] for a in adcs)}")
print("\nSample gyn candidates:")
for a in gyn[:12]:
    print(f"  [{','.join(a['gyn_site_tags']):14s}] {a['name'][:45]:45s} {a['slug']}")
