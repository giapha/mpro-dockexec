#!/usr/bin/env python3
"""Aggregate the scaled audit workflow output → method_audit_scaled.csv + STATS_scaled.md/json.
Usage: python aggregate_scaled_audit.py <workflow_output_json>"""
import json,sys,csv,os,math,collections
OUT=os.path.dirname(os.path.abspath(__file__))
PKG=os.path.join(OUT,"..")
def wilson(k,n):
    if n==0: return (0,0)
    z=1.96; p=k/n; d=1+z*z/n
    c=(p+z*z/(2*n))/d; h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return (round(100*(c-h),1),round(100*(c+h),1))
FIELDS=["pdb_receptor","protein_chain","ligand_identifier","docking_software","software_version","grid_center","grid_size","search_effort","random_seed","receptor_preparation","ligand_preparation","protonation_tautomer","water_ion_handling","validation_redocking","code_artifacts","numeric_result"]

# merge: accumulator (first batch) + any workflow outputs passed as args
CL=os.path.join(PKG,"02_corpus_lock")
merged={}
accum_p=os.path.join(CL,"audits_accum.json")
if os.path.exists(accum_p):
    for k,v in json.load(open(accum_p)).items(): merged[int(v["paper_idx"])]=v
for src in sys.argv[1:]:
    o=json.load(open(src)); r=o["result"]; r=json.loads(r) if isinstance(r,str) else r
    for a in r.get("audits",[]): merged[int(a["paper_idx"])]=a
audits=list(merged.values())
print(f"merged audits total: {len(audits)} (accum + {len(sys.argv)-1} workflow output(s))")
# keep only confirmed Mpro docking originals
A=[a for a in audits if a.get("is_mpro_docking")]
dropped=len(audits)-len(A)
print(f"confirmed Mpro-docking originals: {len(A)}  (dropped non-eligible at full text: {dropped})")

# per-paper CSV
with open(os.path.join(OUT,"method_audit_scaled.csv"),"w",newline="") as f:
    w=csv.writer(f); w.writerow(["paper_idx","target_pdb","software","paper_e_class","blocking_field","n_ligand_claims"]+FIELDS)
    for a in A:
        fl=a.get("fields",{})
        w.writerow([a["paper_idx"],a.get("target_pdb",""),a.get("software",""),a["paper_e_class"],a.get("blocking_field",""),a.get("n_ligand_claims",0)]+[fl.get(k,"missing") for k in FIELDS])

N=len(A)
# reporting completeness (reported only; partial counted separately)
fieldstat={}
for k in FIELDS:
    rep=sum(1 for a in A if a.get("fields",{}).get(k)=="reported")
    par=sum(1 for a in A if a.get("fields",{}).get(k)=="partial")
    fieldstat[k]={"reported":rep,"partial":par,"missing":N-rep-par,"pct_reported":round(100*rep/N,1),"ci":wilson(rep,N),"pct_rep_or_partial":round(100*(rep+par)/N,1)}
# paper-level E dist
ep=collections.Counter(a["paper_e_class"] for a in A)
# claim-weighted E dist
ec=collections.Counter(); tot_claims=0
for a in A:
    n=max(a.get("n_ligand_claims",0),0); ec[a["paper_e_class"]]+=n; tot_claims+=n
stats={"N_papers":N,"N_dropped_noneligible":dropped,"N_claims_est":tot_claims,
  "paper_E":{k:{"n":ep.get(k,0),"pct":round(100*ep.get(k,0)/N,1),"ci":wilson(ep.get(k,0),N)} for k in ["E0","E1","E2","E3","E4"]},
  "claim_E":{k:{"n":ec.get(k,0),"pct":round(100*ec.get(k,0)/tot_claims,1) if tot_claims else 0} for k in ["E0","E1","E2","E3","E4"]},
  "fields":fieldstat}
json.dump(stats,open(os.path.join(OUT,"stats_scaled.json"),"w"),indent=1)

lines=[f"# Paper 1 — SCALED audit statistics (N={N} papers, ~{tot_claims} claims)","",
  f"Confirmed SARS-CoV-2 Mpro docking originals: **{N}** (dropped {dropped} non-eligible at full text).","",
  "## Paper-level executability E0–E4"]
for k in ["E0","E1","E2","E3","E4"]:
    s=stats["paper_E"][k]; lines.append(f"- {k}: {s['n']}/{N} = {s['pct']}% (95% CI {s['ci'][0]}–{s['ci'][1]})")
lines+=["","## Claim-weighted executability"]
for k in ["E0","E1","E2","E3","E4"]:
    s=stats["claim_E"][k]; lines.append(f"- {k}: {s['n']}/{tot_claims} = {s['pct']}%")
lines+=["","## Reporting completeness (16 fields, ranked)","| field | reported | % | 95% CI | +partial |","|---|---:|---:|---|---:|"]
for k,v in sorted(fieldstat.items(),key=lambda kv:kv[1]["pct_reported"]):
    lines.append(f"| {k} | {v['reported']}/{N} | {v['pct_reported']}% | {v['ci'][0]}–{v['ci'][1]} | {v['pct_rep_or_partial']}% |")
lines+=["",f"## vs pilot (N=33): paper-level E1 21.2% / E2 60.6% / E3 18.2% → scaled E1 {stats['paper_E']['E1']['pct']}% / E2 {stats['paper_E']['E2']['pct']}% / E3 {stats['paper_E']['E3']['pct']}%"]
open(os.path.join(OUT,"STATS_scaled.md"),"w").write("\n".join(lines))
print("\n".join(lines[:14]))
print(f"\nwrote method_audit_scaled.csv, stats_scaled.json, STATS_scaled.md")
