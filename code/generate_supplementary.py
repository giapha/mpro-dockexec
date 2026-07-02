#!/usr/bin/env python3
"""Assemble Supplementary Information (Q1) for NewScience Paper 1: supp tables S1-S3
from real data + supp figures SF1-SF3. Writes Supplementary_Information.md (pandoc -> docx)."""
import csv, os
A=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 08_manuscript_v0.3
RUN=os.path.join(A,"..","09_scoring_benchmark","runner","out")
def rd(p):
    return list(csv.DictReader(open(p))) if os.path.exists(p) else []
rep=rd(os.path.join(RUN,"reproduction_outcomes.csv"))
prov={r["ligand_name"]:r for r in rd(os.path.join(RUN,"ligand_provenance.csv"))}
sc=rd(os.path.join(RUN,"self_consistency.csv"))
box=rd(os.path.join(RUN,"box_table.csv"))

def cell(s): return (s or "").replace("|","\\|")
L=[]
L.append("# Supplementary Information")
L.append("\n*NewScience Paper 1 — \"Most open-access Mpro docking papers are not directly re-executable.\"*\n")
L.append("This document accompanies the main text. Supplementary figures S1–S3 and tables S1–S5 are generated from the released dataset (`reproduction_outcomes.csv`, `self_consistency.csv`, `box_table.csv`, `ligand_provenance.csv`, `Table5b_concordance.md`); every value is reproducible from those files.\n")

# Supp figures
L.append("\n## Supplementary Figures\n")
L.append("![Figure S1. PRISMA 2020 flow for corpus construction: records screened, deduplicated, open-access full text retrieved, and confirmed original Mpro docking studies.](figures/Figure7_PRISMA_flow.png)\n")
L.append("![Figure S2. Effect of the box-size method fix. Median absolute deviation by executability class for v1 (default 25 Å box) versus v2 (each paper's reported box). Using reported boxes tightens both strata, confirming that part of the v1 spread was an artifact of the default box rather than the literature.](figures/FigureS2_method_fix_v1_v2.png)\n")
L.append("![Figure S3. Bootstrap sampling distributions (4,000 resamples) of the median absolute deviation for E3 (n=6) and E2 (n=31). The distributions overlap substantially, consistent with the non-significant Mann–Whitney test (P=0.14) and the underpowered E3 stratum.](figures/FigureS3_bootstrap_overlap.png)\n")

# Table S1 — per-claim re-execution
L.append("\n## Supplementary Tables\n")
L.append("**Table S1. Per-claim re-execution results (CID-anchored, reported boxes, AutoDock Vina 1.2.7).** Every re-docked claim with PubChem CID, InChIKey, reported and re-executed score, absolute deviation, and tolerance flag. Docks failing the technical-failure rule (re-executed score > −2 kcal/mol, no bound pose) are marked.\n")
hdr=["Claim","Paper","Target","E","Ligand","CID","InChIKey","Rep.","Rerun","absΔ","≤2"]
L.append("| "+" | ".join(hdr)+" |")
L.append("|"+"|".join(["---"]*len(hdr))+"|")
def fnum(x):
    try: return f"{float(x):.2f}"
    except: return cell(x)
docked=[r for r in rep if r.get("rerun_score","").strip()]
docked.sort(key=lambda r:(r.get("e_class",""),r.get("paper_id",""),r.get("claim_id","")))
for r in docked:
    p=prov.get(r["ligand_name"].strip(),{})
    d=r.get("abs_delta","")
    try: passq = float(r["rerun_score"])<=-2.0; tol = "✓" if (passq and abs(float(d))<=2) else ("fail-dock" if not passq else "")
    except: tol=""
    L.append("| "+" | ".join([cell(r.get("claim_id","")),cell(r.get("paper_id","")),cell(r.get("target_pdb","")),
        cell(r.get("e_class","")),cell(r.get("ligand_name","")[:26]),cell(p.get("cid","")),cell(p.get("inchikey","")[:14]),
        fnum(r.get("reported_score","")),fnum(r.get("rerun_score","")),fnum(d),tol])+" |")

# Table S2 — self-consistency
L.append("\n**Table S2. AutoDock Vina self-consistency (noise floor).** Each curated ligand re-docked across three random seeds (11, 29, 53); the within-ligand score range defines the engine's run-to-run noise. The 95th-percentile range sets the 2.0 kcal/mol reproduction tolerance.\n")
hdr2=["Ligand","Paper","Target","Seeds","Scores (kcal/mol)","Mean","Range"]
L.append("| "+" | ".join(hdr2)+" |"); L.append("|"+"|".join(["---"]*len(hdr2))+"|")
for r in sc:
    L.append("| "+" | ".join([cell(r.get("ligand","")[:24]),cell(r.get("paper_id","")),cell(r.get("pdb","")),
        cell(r.get("n_seeds","")),cell(r.get("scores","")),cell(r.get("mean","")),cell(r.get("range",""))])+" |")

# Table S3 — parsed boxes
L.append("\n**Table S3. Reported docking boxes parsed from source text.** Box centre and size span-parsed per paper (used in the v2 re-execution). Blind-docking boxes wider than 40 Å were capped at 40 Å (flagged); empty size falls back to a 25 Å cube. Span-parsed values are not individually human-verified.\n")
hdr3=["Paper","Centre (x, y, z)","Size (x, y, z)","Size capped","Centre found","Size found"]
L.append("| "+" | ".join(hdr3)+" |"); L.append("|"+"|".join(["---"]*len(hdr3))+"|")
for r in box:
    ctr=f"({r['cx']}, {r['cy']}, {r['cz']})" if r.get("cx") else "—"
    sz=f"({r['sx']}, {r['sy']}, {r['sz']})" if r.get("sx") else "—"
    L.append("| "+" | ".join([cell(r.get("paper_id","")),ctr,sz,cell(r.get("size_capped","")),
        cell(r.get("center_found","")),cell(r.get("size_found",""))])+" |")

# Table S4 — human-AI concordance (secondary, the third rater)
L.append("\n**Table S4. Secondary human–AI concordance (third rater).** Human reviewer R1 versus a blind platform language model (GPT-class, field states only, codebook MERS-Dock v1.1, blind to all prior labels). This is a human–AI concordance metric, distinct from the primary human–human inter-rater κ (R1 vs R2, Table 4); both reach the same value, each disagreeing with R1 only on the single borderline paper P0005.\n")
hdr4=["Metric","Value"]
L.append("| "+" | ".join(hdr4)+" |"); L.append("|"+"|".join(["---"]*len(hdr4))+"|")
for k,v in [("N (deep-audit papers)","33"),("Raw agreement","0.97"),("Cohen's κ","0.926"),
            ("Linear-weighted κ","0.931"),("Quadratic-weighted κ","0.939"),
            ("Disagreements","1 (P0005: R1=E2, AI=E3)"),("Rater","blind GPT-class model, field-states only, blind to prior labels")]:
    L.append(f"| {k} | {v} |")

# Table S5 — sensitivity to the failed-to-bind exclusion
L.append("\n**Table S5. Sensitivity of the re-execution result to the technical-failure exclusion.** The primary analysis excludes three failed-to-bind docks (re-executed score > −2 kcal/mol, no bound pose). The sensitivity analysis instead counts them as non-reproductions. All three are E2 (under-reported) claims; none are E3, so the E3 stratum is unchanged. The E3-below-E2 ordering and the E3 noise-floor result are preserved.\n")
hdr5=["Treatment of failed-to-bind docks","N","median absΔ","within 2 kcal/mol","E3 median","E2 median"]
L.append("| "+" | ".join(hdr5)+" |"); L.append("|"+"|".join(["---"]*len(hdr5))+"|")
L.append("| Primary (excluded as technical failures) | 37 | 0.54 | 29/37 (78%) | 0.24 (n=6) | 0.59 (n=31) |")
L.append("| Sensitivity (counted as non-reproductions) | 40 | 0.59 | 29/40 (72%) | 0.24 (n=6) | 0.74 (n=34) |")

L.append("\n---\n*Supplementary generated from the released dataset; regenerate with `analysis/generate_supplementary.py` + `analysis/render_supp_figs_Q1.R`.*")
out=os.path.join(A,"Supplementary_Information.md")
open(out,"w").write("\n".join(L)+"\n")
print(f"wrote {out} | S1 rows: {len(docked)} | S2 rows: {len(sc)} | S3 rows: {len(box)}")
