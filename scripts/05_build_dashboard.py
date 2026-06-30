#!/usr/bin/env python3
"""Generate a single self-contained interactive HTML dashboard from gyn_final.json.
Features: target-antigen filter + live aggregation panels (target/phase/company/subtype)
+ a Korean/English UI toggle (top-right). Drug names, company names and trial/paper
titles are NOT translated; UI chrome and controlled vocabulary (status/phase/subtype) are."""
import json, datetime
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "gyn_final.json"
OUT = ROOT / "output" / "adc_gyn_dashboard.html"

drugs = json.loads(SRC.read_text())
built = datetime.date.today().isoformat()

n_total = len(drugs)
n_both = sum(d["site_tagged_gyn"] and d["ctgov_confirmed"] for d in drugs)
n_site = sum(d["site_tagged_gyn"] and not d["ctgov_confirmed"] for d in drugs)
n_ct = sum(not d["site_tagged_gyn"] and d["ctgov_confirmed"] for d in drugs)
n_trials = sum(d["n_gyn_trials"] for d in drugs)
n_papers = len({p["pmid"] for d in drugs for p in d.get("papers", [])})
n_targets = len({d.get("target", "Other / unspecified") for d in drugs})

DATA = json.dumps(drugs, ensure_ascii=False)

# ---- i18n dictionary ----
I18N = {
  "en": {
    "title": "Gynecologic-Oncology ADC Map",
    "subtitle": "Antibody-drug conjugates with ovarian / endometrial / cervical / other gynecologic relevance — linked to ClinicalTrials.gov &amp; PubMed · built " + built,
    "s_total": "Gyn ADCs", "s_both": "Tag + Trial", "s_site": "Tag only",
    "s_ct": "Trial only*", "s_trials": "Gyn trials", "s_papers": "PubMed papers",
    "legend": "* \"Trial only\" = found via ClinicalTrials.gov reverse search but NOT tagged on adcreview.com (e.g. cervical, which the site has no tag for).",
    "search_ph": "Search drug, company, target, NCT, condition…",
    "all_sources": "All sources", "src_both": "Tag + Trial", "src_site": "Site tag only", "src_ct": "CT.gov only",
    "any_status": "Any trial status", "any_target": "All targets", "any_phase": "Any phase",
    "has_trial": "has trial", "has_paper": "has paper",
    "summary": "▸ Summary", "summary_open": "▾ Summary",
    "agg_target": "By target", "agg_phase": "By phase", "agg_company": "By company", "agg_subtype": "By subtype",
    "th_drug": "Drug", "th_company": "Company", "th_target": "Target", "th_payload": "Payload",
    "th_subtype": "Gyn subtype", "th_trials": "Trials", "th_phase": "Phase", "th_papers": "Papers", "th_source": "Source",
    "any_payload": "All payloads", "agg_payload": "By payload",
    "empty": "No ADCs match the current filters.",
    "profile": "↗ adcreview.com profile",
    "d_trials": "Gynecologic clinical trials", "d_papers": "Linked literature",
    "no_trials": "No gynecologic trials matched on ClinicalTrials.gov.",
    "no_papers": "No linked PubMed papers found.",
    "ref_trial": "◆ trial ref", "ref_search": "○ search", "sponsor": "Sponsor", "since": "since",
    "reset": "Reset filters", "showing": "showing",
    "footer": "Source catalog: adcreview.com ADC Drug Map · Trials: ClinicalTrials.gov API v2 · Literature: NCBI PubMed E-utilities. Hybrid method: site organ-tags (ovaries/uterus) validated and extended by ClinicalTrials.gov intervention searches post-filtered on gynecologic conditions. Not medical advice; verify trial status before use.",
    "lang_btn": "한국어",
  },
  "ko": {
    "title": "부인암 ADC 맵",
    "subtitle": "난소 / 자궁내막 / 자궁경부 / 기타 부인암과 관련된 항체-약물 접합체(ADC) — ClinicalTrials.gov 및 PubMed 연계 · 생성일 " + built,
    "s_total": "부인암 ADC", "s_both": "태그+임상", "s_site": "태그만",
    "s_ct": "임상만*", "s_trials": "부인암 임상", "s_papers": "PubMed 논문",
    "legend": "* \"임상만\" = adcreview.com에는 부인암 태그가 없지만 ClinicalTrials.gov 역방향 검색으로 찾은 약제 (예: 사이트에 태그가 없는 자궁경부암).",
    "search_ph": "약제·기업·타깃·NCT·적응증 검색…",
    "all_sources": "모든 출처", "src_both": "태그+임상", "src_site": "사이트 태그만", "src_ct": "CT.gov만",
    "any_status": "모든 임상 상태", "any_target": "모든 타깃", "any_phase": "모든 상(phase)",
    "has_trial": "임상 있음", "has_paper": "논문 있음",
    "summary": "▸ 통계", "summary_open": "▾ 통계",
    "agg_target": "타깃별", "agg_phase": "상(phase)별", "agg_company": "기업별", "agg_subtype": "아형별",
    "th_drug": "약제", "th_company": "기업", "th_target": "타깃", "th_payload": "페이로드",
    "th_subtype": "부인암 아형", "th_trials": "임상", "th_phase": "상", "th_papers": "논문", "th_source": "출처",
    "any_payload": "모든 페이로드", "agg_payload": "페이로드별",
    "empty": "현재 필터에 해당하는 ADC가 없습니다.",
    "profile": "↗ adcreview.com 프로필",
    "d_trials": "부인암 임상시험", "d_papers": "연계 문헌",
    "no_trials": "ClinicalTrials.gov에서 일치하는 부인암 임상이 없습니다.",
    "no_papers": "연계된 PubMed 논문이 없습니다.",
    "ref_trial": "◆ 임상 참고문헌", "ref_search": "○ 검색", "sponsor": "스폰서", "since": "시작",
    "reset": "필터 초기화", "showing": "표시",
    "footer": "출처: adcreview.com ADC Drug Map · 임상: ClinicalTrials.gov API v2 · 문헌: NCBI PubMed E-utilities. 하이브리드 방법: 사이트 장기 태그(난소/자궁)를 ClinicalTrials.gov intervention 검색(부인암 condition 사후 필터)으로 검증·확장. 의학적 조언이 아니며, 사용 전 임상 상태를 확인하세요.",
    "lang_btn": "English",
  },
}
# controlled-vocabulary translations used by JS
VOCAB = {
  "subtype": {
    "ovarian": ["Ovarian", "난소"], "endometrial": ["Endometrial", "자궁내막"],
    "cervical": ["Cervical", "자궁경부"], "vulvar_vaginal": ["Vulvar/Vaginal", "외음/질"],
    "gtn": ["GTN", "융모성(GTN)"], "gyn_other": ["Other gyn", "기타 부인과"],
  },
  "status": {
    "RECRUITING": ["Recruiting", "모집중"], "ACTIVE_NOT_RECRUITING": ["Active", "진행중(모집종료)"],
    "COMPLETED": ["Completed", "완료"], "NOT_YET_RECRUITING": ["Not yet recruiting", "모집예정"],
    "TERMINATED": ["Terminated", "중단"], "WITHDRAWN": ["Withdrawn", "철회"],
    "SUSPENDED": ["Suspended", "보류"], "UNKNOWN": ["Unknown", "불명"],
    "ENROLLING_BY_INVITATION": ["By invitation", "초청 등록"], "AVAILABLE": ["Available", "이용가능"],
  },
  "phase": {
    "EARLY_PHASE1": ["Early Ph1", "초기 1상"], "PHASE1": ["Phase 1", "1상"],
    "PHASE2": ["Phase 2", "2상"], "PHASE3": ["Phase 3", "3상"], "PHASE4": ["Phase 4", "4상"],
    "NA": ["N/A", "해당없음"],
  },
  "source": {
    "both": ["Tag + Trial", "태그+임상"], "site": ["Tag only", "태그만"], "ct": ["CT.gov only", "임상만"],
  },
}

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>
:root{--bg:#0f1419;--card:#1a212b;--card2:#232c38;--line:#2e3a48;--txt:#e6edf3;--mut:#8b98a8;--accent:#5eb0ef;--ok:#3fb950;--warn:#d29922;--pink:#f778ba;}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--txt);font:14px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Apple SD Gothic Neo","Malgun Gothic",sans-serif}
header{padding:20px 24px;border-bottom:1px solid var(--line);background:linear-gradient(180deg,#16202b,#0f1419);position:relative}
h1{margin:0 0 4px;font-size:20px}
.sub{color:var(--mut);font-size:12.5px}
#langtog{position:absolute;top:18px;right:24px;background:var(--card);color:var(--txt);border:1px solid var(--accent);border-radius:20px;padding:7px 16px;font-size:13px;cursor:pointer;font-weight:600}
#langtog:hover{background:var(--accent);color:#06121f}
.stats{display:flex;gap:10px;flex-wrap:wrap;margin-top:14px}
.stat{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:8px 14px;min-width:90px}
.stat b{font-size:20px;display:block}
.stat span{color:var(--mut);font-size:11px;text-transform:uppercase;letter-spacing:.04em}
.controls{display:flex;gap:10px;flex-wrap:wrap;align-items:center;padding:14px 24px;position:sticky;top:0;background:rgba(15,20,25,.96);backdrop-filter:blur(6px);border-bottom:1px solid var(--line);z-index:10}
input[type=search],select{background:var(--card);color:var(--txt);border:1px solid var(--line);border-radius:8px;padding:8px 10px;font-size:13px}
input[type=search]{min-width:220px;flex:1}
.chip{padding:5px 11px;border-radius:20px;border:1px solid var(--line);background:var(--card);cursor:pointer;font-size:12px;user-select:none}
.chip.on{background:var(--accent);color:#06121f;border-color:var(--accent);font-weight:600}
.btn{padding:7px 13px;border-radius:8px;border:1px solid var(--line);background:var(--card);color:var(--txt);cursor:pointer;font-size:12.5px}
.btn:hover{border-color:var(--accent)}
#aggpanel{padding:6px 24px 0;display:none}
#aggpanel.open{display:block}
.agggrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:14px;padding:12px 0}
.aggcard{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:10px 12px}
.aggcard h4{margin:0 0 8px;font-size:11px;text-transform:uppercase;letter-spacing:.05em;color:var(--mut)}
.aggrow{display:flex;align-items:center;gap:8px;padding:2px 0;cursor:pointer;font-size:12.5px}
.aggrow:hover .agglabel{color:var(--accent)}
.agglabel{flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.aggbar{height:7px;background:var(--accent);border-radius:4px;opacity:.7;min-width:3px}
.aggn{color:var(--mut);font-variant-numeric:tabular-nums;width:26px;text-align:right}
.wrap{padding:8px 24px 60px}
.countline{color:var(--mut);font-size:12px;padding:6px 2px}
table{width:100%;border-collapse:collapse}
th{text-align:left;color:var(--mut);font-size:11px;text-transform:uppercase;letter-spacing:.04em;padding:8px 10px;border-bottom:1px solid var(--line);cursor:pointer;white-space:nowrap}
td{padding:9px 10px;border-bottom:1px solid #1f2731;vertical-align:top}
tr.row{cursor:pointer}
tr.row:hover{background:var(--card)}
.name{font-weight:600}
.co{color:var(--mut);font-size:12px}
.tgt{display:inline-block;padding:1px 8px;border-radius:12px;font-size:11.5px;background:#13283b;color:#7fc8ff;border:1px solid #244a63}
.pay{display:inline-block;padding:1px 8px;border-radius:12px;font-size:11.5px;background:#2a2417;color:#e8c37a;border:1px solid #4d4326;white-space:nowrap}
.badge{display:inline-block;padding:1px 8px;border-radius:12px;font-size:11px;margin:1px 3px 1px 0;white-space:nowrap}
.b-ovarian{background:#3a2230;color:#f778ba;border:1px solid #5e2d44}
.b-endometrial{background:#2a2440;color:#bc8cff;border:1px solid #3f3568}
.b-cervical{background:#13343b;color:#56d4dd;border:1px solid #1f5560}
.b-vulvar_vaginal{background:#34291a;color:#e3a857;border:1px solid #56401f}
.b-gtn{background:#1f3326;color:#56d364;border:1px solid #2c5135}
.b-gyn_other{background:#262c36;color:#adbac7;border:1px solid #38414c}
.src{font-size:11px;padding:1px 7px;border-radius:10px;border:1px solid var(--line);white-space:nowrap}
.src.both{color:var(--ok);border-color:#23502f}
.src.site{color:var(--warn)}
.src.ct{color:var(--accent)}
.num{text-align:center;font-variant-numeric:tabular-nums}
.detail{background:var(--card)}
.detail td{padding:0}
.dbox{padding:14px 18px;border-left:3px solid var(--accent);margin:6px 0 6px 8px}
.dsum{color:#c9d4df;margin-bottom:12px;font-size:13px}
.dh{font-size:11px;text-transform:uppercase;letter-spacing:.05em;color:var(--mut);margin:12px 0 6px}
.trial,.paper{background:var(--card2);border:1px solid var(--line);border-radius:8px;padding:9px 12px;margin-bottom:7px}
.trial a,.paper a,a.nct{color:var(--accent);text-decoration:none}
a:hover{text-decoration:underline}
.t-meta{color:var(--mut);font-size:12px;margin-top:3px}
.pill{font-size:10.5px;padding:1px 7px;border-radius:10px;border:1px solid var(--line);margin-right:5px}
.st-RECRUITING,.st-ACTIVE_NOT_RECRUITING,.st-NOT_YET_RECRUITING{color:var(--ok);border-color:#23502f}
.st-COMPLETED{color:var(--accent)}
.st-TERMINATED,.st-WITHDRAWN,.st-SUSPENDED{color:#f85149;border-color:#5e2326}
.tag-trial{color:var(--ok)}.tag-search{color:var(--mut)}
.empty{color:var(--mut);font-style:italic;padding:40px;text-align:center}
.hide{display:none}
footer{color:var(--mut);font-size:11.5px;padding:18px 24px;border-top:1px solid var(--line)}
.legend{font-size:11px;color:var(--mut);margin-top:6px}
</style>
</head>
<body>
<header>
  <button id="langtog"></button>
  <h1 data-i18n="title"></h1>
  <div class="sub" data-i18n="subtitle" data-html="1"></div>
  <div class="stats">
    <div class="stat"><b>__N_TOTAL__</b><span data-i18n="s_total"></span></div>
    <div class="stat"><b style="color:var(--ok)">__N_BOTH__</b><span data-i18n="s_both"></span></div>
    <div class="stat"><b style="color:var(--warn)">__N_SITE__</b><span data-i18n="s_site"></span></div>
    <div class="stat"><b style="color:var(--accent)">__N_CT__</b><span data-i18n="s_ct"></span></div>
    <div class="stat"><b>__N_TRIALS__</b><span data-i18n="s_trials"></span></div>
    <div class="stat"><b>__N_PAPERS__</b><span data-i18n="s_papers"></span></div>
  </div>
  <div class="legend" data-i18n="legend"></div>
</header>
<div class="controls">
  <input id="q" type="search">
  <span class="chip subf" data-s="ovarian"></span>
  <span class="chip subf" data-s="endometrial"></span>
  <span class="chip subf" data-s="cervical"></span>
  <span class="chip subf" data-s="vulvar_vaginal"></span>
  <span class="chip subf" data-s="gtn"></span>
  <select id="targetf"></select>
  <select id="payloadf"></select>
  <select id="srcf"></select>
  <select id="statusf"></select>
  <select id="phasef"></select>
  <label class="chip" style="cursor:pointer"><input type="checkbox" id="hastrial"> <span data-i18n="has_trial"></span></label>
  <label class="chip" style="cursor:pointer"><input type="checkbox" id="haspaper"> <span data-i18n="has_paper"></span></label>
  <button class="btn" id="aggbtn"></button>
  <button class="btn" id="resetbtn"></button>
</div>
<div id="aggpanel"><div class="agggrid" id="agggrid"></div></div>
<div class="wrap">
<div class="countline" id="countline"></div>
<table id="tbl">
<thead><tr>
  <th data-k="name" data-i18n="th_drug"></th>
  <th data-k="company" data-i18n="th_company"></th>
  <th data-k="target" data-i18n="th_target"></th>
  <th data-k="payload" data-i18n="th_payload"></th>
  <th data-i18n="th_subtype"></th>
  <th data-k="n_gyn_trials" class="num" data-i18n="th_trials"></th>
  <th data-i18n="th_phase"></th>
  <th data-k="npapers" class="num" data-i18n="th_papers"></th>
  <th data-i18n="th_source"></th>
</tr></thead>
<tbody id="body"></tbody>
</table>
<div id="empty" class="empty hide"></div>
</div>
<footer data-i18n="footer"></footer>
<script>
const DATA = __DATA__;
const I18N = __I18N__;
const VOCAB = __VOCAB__;
let lang = localStorage.getItem('adcgyn_lang') || 'en';
const t = k => (I18N[lang]||I18N.en)[k] ?? k;
const tv = (cat,key) => { const m=VOCAB[cat]&&VOCAB[cat][key]; return m?m[lang==='ko'?1:0]:key; };
const srcOf = d => d.site_tagged_gyn && d.ctgov_confirmed ? 'both' : (d.site_tagged_gyn ? 'site' : 'ct');
let sortK='n_gyn_trials', sortDir=-1, activeSubs=new Set();

const $=id=>document.getElementById(id);
const body=$('body');
function esc(s){return (s||'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]))}

// ---------- filters ----------
function passes(d){
  const q=$('q').value.toLowerCase().trim();
  const srcf=$('srcf').value, statusf=$('statusf').value, targetf=$('targetf').value, payloadf=$('payloadf').value, phasef=$('phasef').value;
  const ht=$('hastrial').checked, hp=$('haspaper').checked;
  if(activeSubs.size && !d.gyn_subtypes.some(s=>activeSubs.has(s))) return false;
  if(srcf && srcOf(d)!==srcf) return false;
  if(statusf && !(d.statuses||[]).includes(statusf)) return false;
  if(targetf && (d.target||'Other / unspecified')!==targetf) return false;
  if(payloadf && (d.payload||'Other / unspecified')!==payloadf) return false;
  if(phasef && !(d.phases||[]).includes(phasef)) return false;
  if(ht && d.n_gyn_trials===0) return false;
  if(hp && !(d.papers||[]).length) return false;
  if(q){
    const hay=[d.name,d.name_full,d.company,d.target,d.payload,d.site_summary,...(d.gyn_subtypes||[]),
      ...(d.trials||[]).map(tr=>tr.nct+' '+tr.title+' '+(tr.conditions||[]).join(' ')),
      ...(d.papers||[]).map(p=>p.title+' '+p.pmid)].join(' ').toLowerCase();
    if(!hay.includes(q)) return false;
  }
  return true;
}

function render(){
  let rows=DATA.filter(passes);
  rows.sort((a,b)=>{
    let av,bv;
    if(sortK==='npapers'){av=(a.papers||[]).length;bv=(b.papers||[]).length;}
    else{av=a[sortK];bv=b[sortK];}
    if(typeof av==='string'){av=av.toLowerCase();bv=(bv||'').toLowerCase();return av<bv?-sortDir:av>bv?sortDir:0;}
    return ((av||0)-(bv||0))*sortDir;
  });
  body.innerHTML='';
  $('empty').classList.toggle('hide',rows.length>0);
  $('countline').textContent=`${t('showing')}: ${rows.length} / ${DATA.length}`;
  for(const d of rows){
    const src=srcOf(d);
    const tr=document.createElement('tr');tr.className='row';
    tr.innerHTML=`<td><div class="name">${esc(d.name)}</div>${d.synonyms&&d.synonyms.length?`<div class="co">${esc(d.synonyms.slice(0,2).join(' | '))}</div>`:''}</td>
      <td class="co">${esc(d.company)}</td>
      <td>${d.target&&d.target!=='Other / unspecified'?`<span class="tgt">${esc(d.target)}</span>`:'<span class="co">—</span>'}</td>
      <td>${d.payload&&d.payload!=='Other / unspecified'?`<span class="pay">${esc(d.payload)}</span>`:'<span class="co">—</span>'}</td>
      <td>${d.gyn_subtypes.map(s=>`<span class="badge b-${s}">${esc(tv('subtype',s))}</span>`).join('')||'<span class="co">—</span>'}</td>
      <td class="num">${d.n_gyn_trials||0}</td>
      <td style="font-size:11.5px">${(d.phases||[]).map(p=>esc(tv('phase',p))).join(', ')||'—'}</td>
      <td class="num">${(d.papers||[]).length}</td>
      <td><span class="src ${src}">${esc(tv('source',src))}</span></td>`;
    const det=document.createElement('tr');det.className='detail hide';
    det.innerHTML=`<td colspan="9">${detailHTML(d)}</td>`;
    tr.onclick=()=>det.classList.toggle('hide');
    body.appendChild(tr);body.appendChild(det);
  }
  renderAgg(rows);
}

function detailHTML(d){
  const trials=(d.trials||[]).map(tr=>`<div class="trial">
    <a class="nct" href="https://clinicaltrials.gov/study/${tr.nct}" target="_blank">${tr.nct}</a>
    <span class="pill st-${esc(tr.status)}">${esc(tv('status',tr.status))}</span>
    ${(tr.phases||[]).map(p=>`<span class="pill">${esc(tv('phase',p))}</span>`).join('')}
    <div style="margin-top:4px">${esc(tr.title)}</div>
    <div class="t-meta">${esc((tr.gyn_conditions||tr.conditions||[]).slice(0,6).join(' · '))}</div>
    <div class="t-meta">${t('sponsor')}: ${esc(tr.sponsor||'—')}${tr.start?' · '+t('since')+' '+esc(tr.start):''}</div>
  </div>`).join('')||`<div class="co">${t('no_trials')}</div>`;
  const papers=(d.papers||[]).map(p=>`<div class="paper">
    <a href="https://pubmed.ncbi.nlm.nih.gov/${p.pmid}/" target="_blank">${esc(p.title||('PMID '+p.pmid))}</a>
    <div class="t-meta">${esc(p.first_author||'')}${p.n_authors>1?' et al.':''} · <i>${esc(p.journal||'')}</i> ${esc(p.year||'')} · PMID ${p.pmid}
      <span class="${p.from_trial?'tag-trial':'tag-search'}">${p.from_trial?t('ref_trial'):t('ref_search')}</span></div>
  </div>`).join('')||`<div class="co">${t('no_papers')}</div>`;
  return `<div class="dbox">
    ${d.site_summary?`<div class="dsum">${esc(d.site_summary)}</div>`:''}
    ${d.target&&d.target!=='Other / unspecified'?`<span class="tgt">${esc(d.target)}</span> `:''}
    ${d.payload&&d.payload!=='Other / unspecified'?`<span class="pay">${esc(d.payload)}</span> `:''}&nbsp;
    <a class="nct" href="${esc(d.url)}" target="_blank">${t('profile')}</a>
    <div class="dh">${t('d_trials')} (${(d.trials||[]).length})</div>${trials}
    <div class="dh">${t('d_papers')} (${(d.papers||[]).length})</div>${papers}
  </div>`;
}

// ---------- aggregation panel ----------
function aggCount(rows, keyfn){
  const c={}; rows.forEach(d=>keyfn(d).forEach(k=>{if(k!=null&&k!=='')c[k]=(c[k]||0)+1;}));
  return Object.entries(c).sort((a,b)=>b[1]-a[1]);
}
function aggCard(titleKey, entries, max, onpick, fmt){
  const top=entries.slice(0,12);
  const rows=top.map(([k,n])=>`<div class="aggrow" data-k="${esc(k)}">
     <span class="agglabel">${esc(fmt?fmt(k):k)}</span>
     <span class="aggbar" style="width:${Math.max(3,Math.round(70*n/max))}px"></span>
     <span class="aggn">${n}</span></div>`).join('');
  const card=document.createElement('div');card.className='aggcard';
  card.innerHTML=`<h4>${t(titleKey)}</h4>${rows||'<div class="co">—</div>'}`;
  card.querySelectorAll('.aggrow').forEach(r=>r.onclick=()=>onpick(r.dataset.k));
  return card;
}
function renderAgg(rows){
  if(!$('aggpanel').classList.contains('open'))return;
  const g=$('agggrid');g.innerHTML='';
  const tEnt=aggCount(rows,d=>[d.target||'Other / unspecified']);
  const yEnt=aggCount(rows,d=>[d.payload||'Other / unspecified']);
  const pEnt=aggCount(rows,d=>d.phases||[]);
  const cEnt=aggCount(rows,d=>[d.company]);
  const sEnt=aggCount(rows,d=>d.gyn_subtypes||[]);
  const mx=a=>a.reduce((m,x)=>Math.max(m,x[1]),1);
  g.appendChild(aggCard('agg_target',tEnt,mx(tEnt),k=>{$('targetf').value=k;render();}));
  g.appendChild(aggCard('agg_payload',yEnt,mx(yEnt),k=>{$('payloadf').value=k;render();}));
  g.appendChild(aggCard('agg_phase',pEnt,mx(pEnt),k=>{$('phasef').value=k;render();},k=>tv('phase',k)));
  g.appendChild(aggCard('agg_company',cEnt,mx(cEnt),k=>{$('q').value=k;render();}));
  g.appendChild(aggCard('agg_subtype',sEnt,mx(sEnt),k=>{activeSubs=new Set([k]);applyStatic();render();},k=>tv('subtype',k)));
}

// ---------- i18n / static UI ----------
function fillSelect(sel, firstKey, pairs){
  const cur=sel.value;
  sel.innerHTML=`<option value="">${t(firstKey)}</option>`+
    pairs.map(([v,label])=>`<option value="${esc(v)}">${esc(label)}</option>`).join('');
  sel.value=cur;
}
function applyStatic(){
  document.documentElement.lang=lang;
  document.querySelectorAll('[data-i18n]').forEach(el=>{
    const s=t(el.dataset.i18n);
    if(el.dataset.html)el.innerHTML=s; else el.textContent=s;
  });
  $('q').placeholder=t('search_ph');
  $('langtog').textContent=t('lang_btn');
  $('aggbtn').textContent=$('aggpanel').classList.contains('open')?t('summary_open'):t('summary');
  $('resetbtn').textContent=t('reset');
  // subtype chips
  document.querySelectorAll('.subf').forEach(c=>{
    c.textContent=tv('subtype',c.dataset.s);
    c.classList.toggle('on',activeSubs.has(c.dataset.s));
  });
  // selects (preserve current value)
  fillSelect($('srcf'),'all_sources',[['both',t('src_both')],['site',t('src_site')],['ct',t('src_ct')]]);
  const targets=[...new Set(DATA.map(d=>d.target||'Other / unspecified'))].sort();
  fillSelect($('targetf'),'any_target',targets.map(x=>[x,x]));
  const payloads=[...new Set(DATA.map(d=>d.payload||'Other / unspecified'))].sort();
  fillSelect($('payloadf'),'any_payload',payloads.map(x=>[x,x]));
  const statuses=[...new Set(DATA.flatMap(d=>d.statuses||[]))].sort();
  fillSelect($('statusf'),'any_status',statuses.map(s=>[s,tv('status',s)]));
  const phases=[...new Set(DATA.flatMap(d=>d.phases||[]))].sort();
  fillSelect($('phasef'),'any_phase',phases.map(p=>[p,tv('phase',p)]));
}

function setLang(l){lang=l;localStorage.setItem('adcgyn_lang',l);applyStatic();render();}

// events
$('langtog').onclick=()=>setLang(lang==='en'?'ko':'en');
['q','srcf','statusf','targetf','payloadf','phasef'].forEach(id=>{$(id).oninput=render;$(id).onchange=render;});
$('hastrial').onchange=render;$('haspaper').onchange=render;
document.querySelectorAll('.subf').forEach(c=>c.onclick=()=>{
  const s=c.dataset.s;if(activeSubs.has(s))activeSubs.delete(s);else activeSubs.add(s);
  c.classList.toggle('on');render();
});
document.querySelectorAll('th[data-k]').forEach(th=>th.onclick=()=>{
  const k=th.dataset.k;if(sortK===k)sortDir*=-1;else{sortK=k;sortDir=(k==='name'||k==='company'||k==='target'||k==='payload')?1:-1;}render();
});
$('aggbtn').onclick=()=>{$('aggpanel').classList.toggle('open');applyStatic();render();};
$('resetbtn').onclick=()=>{
  $('q').value='';activeSubs.clear();
  ['srcf','statusf','targetf','payloadf','phasef'].forEach(id=>$(id).value='');
  $('hastrial').checked=false;$('haspaper').checked=false;applyStatic();render();
};

applyStatic();render();
</script>
</body>
</html>"""

repl = {
    "__TITLE__": I18N["en"]["title"], "__N_TOTAL__": str(n_total), "__N_BOTH__": str(n_both),
    "__N_SITE__": str(n_site), "__N_CT__": str(n_ct), "__N_TRIALS__": str(n_trials),
    "__N_PAPERS__": str(n_papers),
    "__DATA__": DATA, "__I18N__": json.dumps(I18N, ensure_ascii=False),
    "__VOCAB__": json.dumps(VOCAB, ensure_ascii=False),
}
for k, v in repl.items():
    HTML = HTML.replace(k, v)

OUT.write_text(HTML, encoding="utf-8")
# Also publish a copy for GitHub Pages (served from main:/docs).
DOCS = ROOT / "docs"
DOCS.mkdir(exist_ok=True)
(DOCS / "index.html").write_text(HTML, encoding="utf-8")
(DOCS / ".nojekyll").write_text("")
tc = Counter(d.get("target", "Other / unspecified") for d in drugs)
print(f"Dashboard written: {OUT}")
print(f"Pages copy written: {DOCS / 'index.html'}")
print(f"  {n_total} gyn ADCs | {n_trials} trials | {n_papers} papers | {n_targets} distinct targets")
print(f"  top targets: {dict(tc.most_common(6))}")
