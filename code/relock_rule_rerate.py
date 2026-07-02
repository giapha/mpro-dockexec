#!/usr/bin/env python3
"""
Re-lock N=236 E-class labels to the human-aligned deterministic rule classifier.

WHY: On the 33-paper pilot, the original audit pipeline labels agree with the
human reviewer R1 at only Cohen's kappa=0.075 (optimistic outlier), whereas the
deterministic codebook rule classifier reproduces R1 at kappa=0.926 (verified
from analysis/consensus_labels.csv vs analysis/R1_distribution.json; 1 disagreement
P0005). The dev's independent overnight HUMAN re-labelling (R2) also reaches
kappa=0.926 vs R1. The rule is therefore the scalable human-aligned classifier;
the original pipeline `paper_e_class` in method_audit_scaled.csv is superseded.

Rule (identical to synthetic_kappa.py rule_eclass; matches Vincent's R1 policy:
grid-centre-missing -> E1):
  BLOCK any missing (pdb_receptor, grid_center, docking_software) -> E1
  all T1+T2 reported AND random_seed AND code_artifacts reported -> E4
  all ESS reported AND ligand_identifier in (reported, partial)  -> E3
  else -> E2

Deterministic. Stdlib only. Recomputable: python3 relock_rule_rerate.py
Outputs: stats_relocked.json + prints a summary.
"""
import csv, json, math, os
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                              # repo root (parent of code/)
DATA = os.path.join(ROOT, "data", "audit")
SRC = os.path.join(DATA, "paper_audit_N236_field_states.csv")

BLOCK = ["pdb_receptor", "grid_center", "docking_software"]
ESS = ["pdb_receptor", "grid_center", "grid_size", "docking_software",
       "software_version", "receptor_preparation", "ligand_preparation"]
T1 = ["pdb_receptor", "grid_center", "grid_size", "docking_software", "ligand_identifier"]
T2 = ["software_version", "search_effort", "receptor_preparation", "ligand_preparation",
      "protonation_tautomer", "water_ion_handling", "protein_chain"]


def rule_eclass(row):
    g = lambda f: row.get(f, "missing")
    if any(g(f) == "missing" for f in BLOCK):
        return "E1"
    if all(g(f) == "reported" for f in T1 + T2) and g("random_seed") == "reported" and g("code_artifacts") == "reported":
        return "E4"
    if all(g(f) == "reported" for f in ESS) and g("ligand_identifier") in ("reported", "partial"):
        return "E3"
    return "E2"


def wilson(k, n):
    if n == 0:
        return (0.0, 0.0)
    z = 1.959963985
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (round(100 * (c - h), 1), round(100 * (c + h), 1))


def main():
    rows = list(csv.DictReader(open(SRC, encoding="utf-8")))
    N = len(rows)
    ruled = [rule_eclass(r) for r in rows]
    pipeline = [r["paper_e_class"] for r in rows]

    cp = Counter(pipeline)
    cr = Counter(ruled)

    # claim-weighted
    clw = Counter()
    total_claims = 0
    for r, e in zip(rows, ruled):
        try:
            n = int(r.get("n_ligand_claims", "0") or 0)
        except ValueError:
            n = 0
        clw[e] += n
        total_claims += n

    out = {
        "_note": "Human-aligned re-lock of N=236 E-class via deterministic rule classifier "
                 "(rule vs human R1 kappa=0.926). Supersedes optimistic pipeline paper_e_class "
                 "(pipeline vs R1 kappa=0.075). Recompute: python3 relock_rule_rerate.py",
        "N": N,
        "paper_level_rule_relocked": {
            e: {"n": cr[e], "pct": round(100 * cr[e] / N, 1), "wilson95": wilson(cr[e], N)}
            for e in ["E1", "E2", "E3", "E4"]
        },
        "paper_level_pipeline_superseded": {
            e: {"n": cp[e], "pct": round(100 * cp[e] / N, 1)} for e in ["E1", "E2", "E3", "E4"]
        },
        "executable_E3plusE4": {
            "n": cr["E3"] + cr["E4"], "pct": round(100 * (cr["E3"] + cr["E4"]) / N, 1),
            "wilson95": wilson(cr["E3"] + cr["E4"], N),
            "not_executable_pct": round(100 * (N - cr["E3"] - cr["E4"]) / N, 1),
        },
        "claim_weighted_rule": {
            "total_claims_est": total_claims,
            **{e: {"n": clw[e], "pct": round(100 * clw[e] / total_claims, 1)} for e in ["E1", "E2", "E3", "E4"]},
        },
        "disagreements_pipeline_vs_rule": sum(1 for a, b in zip(pipeline, ruled) if a != b),
        "E4_zero_reason": "Only 1 paper reports random_seed (idx 49); its code_artifacts is missing, "
                          "so it does not meet the strict E4 bar (rule -> E3). No paper is fully reproducible.",
    }

    with open(os.path.join(DATA, "stats_relocked.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)

    # human-readable
    print(f"N={N}")
    print("PAPER-LEVEL (rule, human-aligned):")
    for e in ["E1", "E2", "E3", "E4"]:
        d = out["paper_level_rule_relocked"][e]
        print(f"  {e}: {d['n']:3d}  {d['pct']:5.1f}%  CI{d['wilson95']}")
    ex = out["executable_E3plusE4"]
    print(f"  Executable E3+E4: {ex['n']} = {ex['pct']}%  (not executable {ex['not_executable_pct']}%)")
    print("CLAIM-WEIGHTED:", {e: out["claim_weighted_rule"][e]["pct"] for e in ["E1", "E2", "E3", "E4"]})
    print(f"pipeline->rule disagreements: {out['disagreements_pipeline_vs_rule']}/{N}")
    print("-> wrote stats_relocked.json")


if __name__ == "__main__":
    main()
