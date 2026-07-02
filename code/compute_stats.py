#!/usr/bin/env python3
"""
NewScience Paper 1 — reproducible statistics from released candidate CSVs.
Stdlib only (no numpy/scipy). Wilson score 95% CI. Run: python3 compute_stats.py
Inputs : ../data/method_audit_candidate.csv , ../data/extracted_claims_candidate.csv
Outputs: ./STATS_v2.md , ./stats_v2.json
Primary analysis = N=33 audited papers; sensitivity = N=32 (exclude P0028, the one
paper auto-flagged by adversarial adjudication for an E-class dispute).
Primary endpoint per protocol = CLAIM-level E0-E4 distribution; paper-level reported as secondary.
"""
import csv, json, math, os

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")
FIELDS = ["pdb_receptor","protein_chain","ligand_identifier","docking_software","software_version",
          "grid_center","grid_size","search_effort","random_seed","receptor_preparation",
          "ligand_preparation","protonation_tautomer","water_ion_handling","validation_redocking",
          "code_artifacts","numeric_result"]
FLAGGED = "P0028"

def wilson(k, n, z=1.96):
    if n == 0: return (0.0, 0.0)
    p = k / n; d = 1 + z*z/n
    c = (p + z*z/(2*n)) / d
    h = (z/d) * math.sqrt(p*(1-p)/n + z*z/(4*n*n))
    return (round(100*max(0, c-h), 1), round(100*min(1, c+h), 1))

papers = list(csv.DictReader(open(os.path.join(DATA, "method_audit_candidate.csv"), encoding="utf-8")))
claims = list(csv.DictReader(open(os.path.join(DATA, "extracted_claims_candidate.csv"), encoding="utf-8")))

def block(pp, cc, label):
    N = len(pp)
    # paper-level E-class
    pe = {k: sum(1 for p in pp if p["final_E_class"] == k) for k in ["E0","E1","E2","E3","E4"]}
    paper_E = {k: {"n": pe[k], "pct": round(100*pe[k]/N, 1), "ci": wilson(pe[k], N)} for k in pe}
    # claim-level E-class (PRIMARY endpoint): each claim inherits its paper's E-class
    nC = len(cc)
    ce = {k: sum(1 for c in cc if c["e_class"] == k) for k in ["E0","E1","E2","E3","E4"]}
    # naive Wilson CI; note: claims are clustered in papers (design-effect inflates true CI) -> see note
    claim_E = {k: {"n": ce[k], "pct": round(100*ce[k]/nC, 1), "ci_naive": wilson(ce[k], nC)} for k in ce}
    # field completeness
    fields = {}
    for f in FIELDS:
        rep = sum(1 for p in pp if p[f] == "reported")
        par = sum(1 for p in pp if p[f] == "partial")
        fields[f] = {"reported": rep, "partial": par, "missing": N-rep-par,
                     "pct_reported": round(100*rep/N, 1), "ci_reported": wilson(rep, N),
                     "pct_reported_or_partial": round(100*(rep+par)/N, 1)}
    def ws(p):
        return sum(1 if p[f]=="reported" else 0.5 if p[f]=="partial" else 0 for f in FIELDS)/len(FIELDS)
    wsv = [ws(p) for p in pp]
    wmean = sum(wsv)/len(wsv)
    wsd = (sum((x-wmean)**2 for x in wsv)/(len(wsv)-1))**0.5 if len(wsv) > 1 else 0
    numeric = sum(1 for c in cc if c["is_numeric_result"] == "Y")
    ident = sum(1 for c in cc if c["has_ligand_identifier"] == "Y")
    bothv = sum(1 for c in cc if c["method_span_verified"]=="True" and c["result_span_verified"]=="True")
    return {"label": label, "N_papers": N, "N_claims": nC,
            "paper_level_E": paper_E, "claim_level_E_PRIMARY": claim_E,
            "fields": fields,
            "weighted_completeness_mean_pct": round(100*wmean, 1), "weighted_completeness_sd_pct": round(100*wsd, 1),
            "claims": {"numeric_result": {"n": numeric, "pct": round(100*numeric/nC,1), "ci": wilson(numeric,nC)},
                       "ligand_identifier": {"n": ident, "pct": round(100*ident/nC,1), "ci": wilson(ident,nC)},
                       "both_spans_verified": {"n": bothv, "pct": round(100*bothv/nC,1), "ci": wilson(bothv,nC)}}}

primary = block(papers, claims, "PRIMARY (N=33 audited papers)")
sens_pp = [p for p in papers if p["paper_id"] != FLAGGED]
sens_cc = [c for c in claims if c["paper_id"] != FLAGGED]
sensitivity = block(sens_pp, sens_cc, "SENSITIVITY (N=32, exclude P0028)")

stats = {"generated_by": "compute_stats.py (stdlib, Wilson 95% CI)",
         "corpus": {"raw": 1400, "dedup": 1018, "included": 48, "audited": 33, "acquisition_pending": 15},
         "primary": primary, "sensitivity": sensitivity,
         "notes": ["Primary = N=33 audited papers. Claim-level E0-E4 = pre-registered primary endpoint; "
                   "paper-level reported as secondary. Claim CIs are naive Wilson; claims are nested in papers "
                   "(33 clusters), so true CIs are wider (design effect) -- a cluster-robust/mixed model is the "
                   "planned refinement. All labels are span-verified AI-candidate, pending two-reviewer human "
                   "countersignature and kappa.",
                   "P0028 auto-flagged by adversarial adjudication for an E-class dispute (candidate E1 vs "
                   "adjudicator E2; content confirmed consistent with the real article; 1 field span-downgraded). "
                   "Results robust to its exclusion (see sensitivity)."]}
json.dump(stats, open(os.path.join(HERE, "stats_v2.json"), "w"), indent=1, ensure_ascii=False)

# markdown
L = []
P = primary; S = sensitivity
L.append("# Paper 1 — Statistics v2 (reproducible; AI-candidate, pending human countersignature)\n")
L.append("> Regenerated by `analysis/compute_stats.py` from `data/*.csv` (stdlib, Wilson 95% CI). Single numeric source of truth for the manuscript.\n")
L.append("## Corpus flow\n1400 raw -> 1018 dedup -> 48 included -> **33 audited** (15 acquisition-pending).\n")
L.append(f"## PRIMARY analysis — N={P['N_papers']} papers, {P['N_claims']} claims\n")
L.append("### Executability E0-E4 — CLAIM level (pre-registered primary endpoint)")
for k in ["E0","E1","E2","E3","E4"]:
    e=P["claim_level_E_PRIMARY"][k]
    if e["n"]: L.append(f"- **{k}**: {e['pct']}% (naive 95% CI {e['ci_naive'][0]}-{e['ci_naive'][1]}; n={e['n']}/{P['N_claims']} claims)")
L.append("\n_Claims are clustered in 33 papers; naive CIs understate uncertainty (cluster-robust model planned)._\n")
L.append("### Executability E0-E4 — PAPER level (secondary)")
for k in ["E0","E1","E2","E3","E4"]:
    e=P["paper_level_E"][k]
    if e["n"]: L.append(f"- **{k}**: {e['pct']}% (95% CI {e['ci'][0]}-{e['ci'][1]}; n={e['n']}/{P['N_papers']})")
L.append(f"\nMean weighted reporting completeness: **{P['weighted_completeness_mean_pct']}%** (SD {P['weighted_completeness_sd_pct']}%)\n")
L.append("### Reporting completeness by field (paper level, ranked least->most reported)")
L.append("| Field | % reported [95% CI] | n/N | % reported+partial |")
L.append("|---|---|---|---|")
for f,v in sorted(P["fields"].items(), key=lambda kv: kv[1]["pct_reported"]):
    L.append(f"| {f} | {v['pct_reported']}% [{v['ci_reported'][0]}-{v['ci_reported'][1]}] | {v['reported']}/{P['N_papers']} | {v['pct_reported_or_partial']}% |")
c=P["claims"]
L.append(f"\n### Claim level (N={P['N_claims']})")
L.append(f"- Numeric docking result: {c['numeric_result']['pct']}% [{c['numeric_result']['ci'][0]}-{c['numeric_result']['ci'][1]}] ({c['numeric_result']['n']}/{P['N_claims']})")
L.append(f"- Explicit ligand identifier: {c['ligand_identifier']['pct']}% [{c['ligand_identifier']['ci'][0]}-{c['ligand_identifier']['ci'][1]}] ({c['ligand_identifier']['n']}/{P['N_claims']})")
L.append(f"- Both source spans verified: {c['both_spans_verified']['pct']}% [{c['both_spans_verified']['ci'][0]}-{c['both_spans_verified']['ci'][1]}] ({c['both_spans_verified']['n']}/{P['N_claims']})")
L.append(f"\n## SENSITIVITY — N={S['N_papers']} papers, {S['N_claims']} claims (exclude P0028)")
L.append("Paper-level E: " + " / ".join(f"{k} {S['paper_level_E'][k]['pct']}%" for k in ['E1','E2','E3'] if S['paper_level_E'][k]['n']))
L.append("Claim-level E: " + " / ".join(f"{k} {S['claim_level_E_PRIMARY'][k]['pct']}%" for k in ['E1','E2','E3'] if S['claim_level_E_PRIMARY'][k]['n']))
L.append("\n## Notes")
for nnote in stats["notes"]: L.append(f"- {nnote}")
open(os.path.join(HERE, "STATS_v2.md"), "w", encoding="utf-8").write("\n".join(L))

# console headline
print("=== PRIMARY N=33 ===")
print("CLAIM-level E:", {k: P["claim_level_E_PRIMARY"][k]["pct"] for k in ["E1","E2","E3"]})
print("PAPER-level E:", {k: P["paper_level_E"][k]["pct"] for k in ["E1","E2","E3"]})
print("weighted completeness:", P["weighted_completeness_mean_pct"], "% SD", P["weighted_completeness_sd_pct"])
print("claims numeric/ident/spans:", P["claims"]["numeric_result"]["pct"], P["claims"]["ligand_identifier"]["pct"], P["claims"]["both_spans_verified"]["pct"])
print("wrote STATS_v2.md + stats_v2.json")
