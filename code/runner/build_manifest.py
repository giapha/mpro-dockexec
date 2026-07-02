#!/usr/bin/env python3
"""
Build the re-execution MANIFEST for the Arm B runner from Paper 1 audit data.

Selects executable claims (E2/E3/E4) that have a reported docking score + a target
PDB, parses the reported grid box from verified source spans where present, and
emits one row per (paper, ligand) the runner can attempt to reproduce.

This is the bridge from audit -> runner: it does NOT dock (no compute needed);
it produces runner/manifest.csv that reexec_runner.py consumes.

Outputs: runner/manifest.csv  (+ console coverage report)
Stdlib only, deterministic.
"""
import csv
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
P1 = os.path.normpath(os.path.join(HERE, "..", "..", "Paper1_Audit", "_CONTROL", "audit_candidate"))
OUT = os.path.join(HERE, "manifest.csv")

NUM = r"[-+]?\d+\.?\d*"
TRIPLE = re.compile(rf"({NUM})\s*[,;]\s*({NUM})\s*[,;]\s*({NUM})")
LABELED = re.compile(rf"x\s*[=:]?\s*({NUM}).*?y\s*[=:]?\s*({NUM}).*?z\s*[=:]?\s*({NUM})", re.IGNORECASE | re.DOTALL)
SIZE_X = re.compile(rf"({NUM})\s*(?:Å|A)?\s*[x×]\s*({NUM})\s*(?:Å|A)?\s*[x×]\s*({NUM})", re.IGNORECASE)


def _clean(span):
    return (span or "").replace("–", "-").replace("−", "-")


def parse_center(span):
    """Grid CENTER: prefer labeled 'x = .. y = .. z = ..' (avoids grabbing a size/dimension
    triple), else fall back to the first bare comma triple."""
    s = _clean(span)
    if not s:
        return None
    m = LABELED.search(s) or TRIPLE.search(s)
    return tuple(round(float(g), 4) for g in m.groups()) if m else None


def parse_size(span):
    """Grid SIZE: require an 'A x B x C' pattern; validate all positive + plausible (6-60 Å).
    Never accept a comma triple (that is usually the center). Returns None if implausible
    -> caller falls back to the documented default box, flagged as assumed (audit fix)."""
    s = _clean(span)
    if not s:
        return None
    m = SIZE_X.search(s)
    if not m:
        return None
    t = tuple(round(float(g), 4) for g in m.groups())
    if all(6.0 <= abs(v) <= 60.0 and v > 0 for v in t):
        return t
    return None


def main():
    method = {r["paper_id"]: r for r in csv.DictReader(open(os.path.join(P1, "method_audit_candidate.csv"), encoding="utf-8"))}
    claims = list(csv.DictReader(open(os.path.join(P1, "extracted_claims_candidate.csv"), encoding="utf-8")))
    long_rows = list(csv.DictReader(open(os.path.join(P1, "reporting_fields_long.csv"), encoding="utf-8")))

    # grid spans per paper
    span = {}
    for r in long_rows:
        if r["field"] in ("grid_center", "grid_size") and (r.get("span") or "").strip():
            span.setdefault(r["paper_id"], {})[r["field"]] = r["span"].strip()

    rows, skipped = [], {"not_executable": 0, "no_score": 0, "no_pdb": 0, "bad_unit_or_value": 0}
    for c in claims:
        pid = c["paper_id"]
        m = method.get(pid, {})
        e = (m.get("final_E_class") or m.get("candidate_E_class") or "").upper()
        if e not in ("E2", "E3", "E4"):
            skipped["not_executable"] += 1
            continue
        # reported numeric binding score
        val = (c.get("reported_result_value") or "").strip()
        try:
            reported = float(val)
        except ValueError:
            skipped["no_score"] += 1
            continue
        # unit/value guard: docking affinity is negative kcal/mol. Drop non-kcal/mol scoring
        # functions (LibDock/CDOCKER/MM-GBSA), positive, or implausibly large values so a
        # units-category mismatch is not silently scored as a failed reproduction (audit fix).
        unit = (c.get("reported_result_unit") or "").lower()
        if ("kcal" not in unit and unit not in ("", "kcal/mol")) or reported >= 0 or reported < -15:
            skipped["bad_unit_or_value"] += 1
            continue
        pdb = (m.get("pdb_id") or "").strip()
        if not pdb:
            skipped["no_pdb"] += 1
            continue
        # first PDB id token
        pdb_id = re.split(r"[ ,;/]+", pdb)[0].strip().strip(".")
        center = parse_center(span.get(pid, {}).get("grid_center"))
        size = parse_size(span.get(pid, {}).get("grid_size"))
        rows.append({
            "claim_id": c["claim_id"], "paper_id": pid, "e_class": e,
            "target_pdb": pdb_id, "chain": "",
            "ligand_name": c.get("ligand_name", ""), "ligand_id": c.get("ligand_identifier", ""),
            "reported_score": reported, "reported_unit": c.get("reported_result_unit", "kcal/mol"),
            "box_center_x": center[0] if center else "", "box_center_y": center[1] if center else "",
            "box_center_z": center[2] if center else "",
            "box_size_x": size[0] if size else "", "box_size_y": size[1] if size else "",
            "box_size_z": size[2] if size else "",
            "box_size_assumed": "" if size else "default_25",
            "needs": ("" if center else "needs_box_center"),
        })

    cols = ["claim_id", "paper_id", "e_class", "target_pdb", "chain", "ligand_name", "ligand_id",
            "reported_score", "reported_unit", "box_center_x", "box_center_y", "box_center_z",
            "box_size_x", "box_size_y", "box_size_z", "box_size_assumed", "needs"]
    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)

    ready = [r for r in rows if not r["needs"]]
    print(f"Manifest: {len(rows)} executable claims with reported score + PDB -> runner/manifest.csv")
    print(f"  ready to dock (box center parsed): {len(ready)}   needs_box_center: {len(rows)-len(ready)}")
    print(f"  papers: {len(set(r['paper_id'] for r in rows))}   PDBs: {sorted(set(r['target_pdb'] for r in rows))[:8]}...")
    print(f"  skipped: {skipped}")
    print("  NOTE: box centers from auto-parsed spans must be human-verified before scientific reruns (R7).")


if __name__ == "__main__":
    main()
