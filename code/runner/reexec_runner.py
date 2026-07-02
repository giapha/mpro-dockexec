#!/usr/bin/env python3
"""
Arm B re-execution runner (generalized, manifest-driven) — the flagship moat engine.

Scales Paper 1's hardcoded 6LU7 batch into a reusable harness: any target PDB, any
ligand, any reported box. For each manifest row it resolves the ligand, prepares
inputs, runs AutoDock Vina, compares the re-run score to the reported score, and
writes a reproduction outcome + full provenance record. This is the ground truth
for the reproducibility moat ("NSE-Score predicts which claims reproduce").

Modes:
  --dry-run   resolve ligand SMILES + check env/receptor availability, NO docking.
              Runs anywhere (only needs network for PubChem). Use this to see how
              many manifest rows are actually runnable before booking compute.
  (default)   full re-execution. Requires a docking env (AutoDock Vina + RDKit +
              meeko mk_prepare_ligand.py), same as Paper 1's env. Set --bin.

Design choices (match Paper 1 reexec for comparability): seed 200, exhaustiveness 16,
RDKit ETKDGv3 embed, box size default 25^3 when unreported (documented assumption).
Resumable: rows already in reproduction_outcomes.csv are skipped.

Inputs : runner/manifest.csv (from build_manifest.py)
Outputs: runner/out/reproduction_outcomes.csv  +  runner/out/provenance/<claim>.json
Provenance/R7: box centers parsed from spans must be human-verified before a rerun
is treated as scientific evidence; the runner records box_source for audit.
"""
import argparse
import csv
import hashlib
import json
import os
import subprocess
import time
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = os.path.join(HERE, "out")
PROV = os.path.join(OUTDIR, "provenance")
LIG = os.path.join(OUTDIR, "ligands")
REC = os.path.join(HERE, "receptors")  # cache: <PDB>_<chain>.pdbqt (prepped, human-verified)
SEED, EXHAUST, DEFAULT_SIZE = 200, 16, (25.0, 25.0, 25.0)


def sha8(s):
    return hashlib.sha256(str(s).encode("utf-8")).hexdigest()[:8]


def load_smiles_cache():
    """Pre-resolved SMILES (from resolve_smiles.py via system TLS). Avoids dock-env network."""
    p = os.path.join(OUTDIR, "smiles_cache.csv")
    if not os.path.exists(p):
        return {}
    return {r["ligand_key"]: (r["smiles"] or None, r["source"] or "cache")
            for r in csv.DictReader(open(p, encoding="utf-8"))}


def resolve_smiles(name, ligand_id):
    """PubChem name -> SMILES; fall back to a numeric CID in ligand_id. None if unresolved."""
    queries = []
    if name:
        queries.append(("name", name))
    lid = (ligand_id or "").strip()
    if lid.isdigit():
        queries.append(("cid", lid))
    for kind, q in queries:
        for prop in ("IsomericSMILES", "CanonicalSMILES"):
            u = (f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/{kind}/"
                 f"{urllib.parse.quote(q)}/property/{prop}/TXT")
            try:
                with urllib.request.urlopen(u, timeout=25) as r:
                    s = r.read().decode().strip().splitlines()[0].strip()
                    if s:
                        return s, f"pubchem:{kind}:{prop}"
            except Exception:
                continue
    return None, None


def embed_prep_ligand(smiles, key, bin_dir):
    from rdkit import Chem
    from rdkit.Chem import AllChem
    m = Chem.MolFromSmiles(smiles)
    if m is None:
        return None
    m = Chem.AddHs(m)
    p = AllChem.ETKDGv3()
    p.randomSeed = SEED
    if AllChem.EmbedMolecule(m, p) != 0 and AllChem.EmbedMolecule(m, AllChem.ETKDGv2()) != 0:
        return None
    try:
        AllChem.MMFFOptimizeMolecule(m)
    except Exception:
        pass
    os.makedirs(LIG, exist_ok=True)
    sdf = os.path.join(LIG, key + ".sdf")
    Chem.SDWriter(sdf).write(m)
    pdbqt = os.path.join(LIG, key + ".pdbqt")
    subprocess.run([os.path.join(bin_dir, "mk_prepare_ligand.py"), "-i", sdf, "-o", pdbqt],
                   capture_output=True, text=True)
    return pdbqt if os.path.exists(pdbqt) else None


def receptor_path(pdb, chain):
    key = f"{pdb}_{chain}" if chain else pdb
    p = os.path.join(REC, key + ".pdbqt")
    return p if os.path.exists(p) else None


def vina_version(bin_dir):
    try:
        out = subprocess.run([os.path.join(bin_dir, "vina"), "--version"],
                             capture_output=True, text=True, timeout=20)
        return (out.stdout or out.stderr).strip().splitlines()[0]
    except Exception:
        return None


def dock(receptor, ligand_pdbqt, center, size, bin_dir, outp):
    cmd = [os.path.join(bin_dir, "vina"), "--receptor", receptor, "--ligand", ligand_pdbqt,
           "--center_x", str(center[0]), "--center_y", str(center[1]), "--center_z", str(center[2]),
           "--size_x", str(size[0]), "--size_y", str(size[1]), "--size_z", str(size[2]),
           "--seed", str(SEED), "--exhaustiveness", str(EXHAUST), "--out", outp]
    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=int(os.environ.get("DOCK_TIMEOUT", "300")))
    except subprocess.TimeoutExpired:
        return None, "TIMEOUT " + " ".join(cmd)
    if os.path.exists(outp):
        for line in open(outp):
            if line.startswith("REMARK VINA RESULT"):
                return float(line.split()[3]), " ".join(cmd)
    return None, " ".join(cmd)


def load_done(path):
    if not os.path.exists(path):
        return set()
    return {r["claim_id"] for r in csv.DictReader(open(path, encoding="utf-8"))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default=os.path.join(HERE, "manifest.csv"))
    ap.add_argument("--bin", default="/tmp/mm/envs/dock/bin", help="dir with vina + mk_prepare_ligand.py")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--include-needs", action="store_true", help="also attempt rows missing a parsed box")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    os.makedirs(OUTDIR, exist_ok=True)
    os.makedirs(PROV, exist_ok=True)
    rows = [r for r in csv.DictReader(open(args.manifest, encoding="utf-8"))]
    if not args.include_needs:
        rows = [r for r in rows if not r["needs"]]
    if args.limit:
        rows = rows[:args.limit]

    out_csv = os.path.join(OUTDIR, "reproduction_outcomes.csv")
    done = load_done(out_csv) if not args.dry_run else set()
    vv = vina_version(args.bin) if not args.dry_run else None
    env_ok = os.path.exists(os.path.join(args.bin, "vina")) and os.path.exists(os.path.join(args.bin, "mk_prepare_ligand.py"))

    cols = ["claim_id", "paper_id", "e_class", "target_pdb", "ligand_name", "reported_score",
            "rerun_score", "abs_delta", "within_1", "within_2", "status", "smiles_source",
            "box_source", "box_size_assumed", "vina_version"]
    new_rows, dry = [], []
    smi_cache = load_smiles_cache()  # pre-resolved (system TLS); dock-env has no network

    for r in rows:
        cid = r["claim_id"]
        if cid in done:
            continue
        name, lid = r["ligand_name"], r["ligand_id"]
        ck = name or lid
        if ck in smi_cache:
            smi, src = smi_cache[ck]
        elif os.environ.get("OFFLINE_CACHE_ONLY"):
            smi, src = None, "uncached"  # offline: skip network resolution, skip this claim
        else:
            smi, src = resolve_smiles(name, lid)
            smi_cache[ck] = (smi, src)
            time.sleep(0.2)
        rec = receptor_path(r["target_pdb"], r["chain"])
        box_ok = bool(r["box_center_x"])

        if args.dry_run:
            dry.append({"claim_id": cid, "paper_id": r["paper_id"], "pdb": r["target_pdb"],
                        "ligand": name[:30], "smiles_resolved": bool(smi), "smiles_source": src or "",
                        "receptor_cached": bool(rec), "box_parsed": box_ok,
                        "runnable": bool(smi and box_ok)})
            continue

        if not env_ok:
            print("ENV MISSING: vina/mk_prepare_ligand.py not found in --bin. "
                  "Run on the docking env (Paper 1 used conda env 'dock'). Use --dry-run here.")
            return
        prov = {"claim_id": cid, "paper_id": r["paper_id"], "target_pdb": r["target_pdb"],
                "ligand_name": name, "ligand_id": lid, "smiles": smi, "smiles_source": src,
                "reported_score": r["reported_score"], "seed": SEED, "exhaustiveness": EXHAUST,
                "box_center": [r["box_center_x"], r["box_center_y"], r["box_center_z"]],
                "box_size_assumed": r["box_size_assumed"], "vina_version": vv}
        status = None
        rerun = ad = w1 = w2 = ""
        if not smi:
            status = "smiles_unresolved"
        elif not rec:
            status = "needs_prepped_receptor:" + (r["target_pdb"] or "?")
        elif not box_ok:
            status = "needs_box_center"
        else:
            key = f"{cid}_{sha8(smi)}"
            pq = embed_prep_ligand(smi, key, args.bin)
            if not pq:
                status = "ligand_prep_failed"
            else:
                center = (float(r["box_center_x"]), float(r["box_center_y"]), float(r["box_center_z"]))
                size = ((float(r["box_size_x"]), float(r["box_size_y"]), float(r["box_size_z"]))
                        if r["box_size_x"] else DEFAULT_SIZE)
                outp = os.path.join(LIG, key + "_dock.pdbqt")
                score, cmd = dock(rec, pq, center, size, args.bin, outp)
                prov["command"] = cmd
                prov["box_size"] = size
                if score is None or score >= 0.0:
                    # Vina binding affinities are negative; 0.0/positive = no valid pose
                    # (ligand outside box) -> docking FAILURE, not a divergent reproduction.
                    # Most common cause: span-parsed box center does not fit this receptor (R7).
                    status = "dock_failed_no_pose"
                else:
                    reported = float(r["reported_score"])
                    ad = round(abs(score - reported), 3)
                    rerun, w1, w2, status = round(score, 3), int(ad <= 1.0), int(ad <= 2.0), "docked"
        prov["status"] = status
        prov["rerun_score"] = rerun
        prov["abs_delta"] = ad
        json.dump(prov, open(os.path.join(PROV, cid + ".json"), "w"), indent=1)
        new_rows.append({"claim_id": cid, "paper_id": r["paper_id"], "e_class": r["e_class"],
                         "target_pdb": r["target_pdb"], "ligand_name": name, "reported_score": r["reported_score"],
                         "rerun_score": rerun, "abs_delta": ad, "within_1": w1, "within_2": w2,
                         "status": status, "smiles_source": src or "", "box_source": "span_parsed",
                         "box_size_assumed": r["box_size_assumed"], "vina_version": vv or ""})
        print(json.dumps({"claim_id": cid, "status": status, "delta": ad}))

    if args.dry_run:
        drp = os.path.join(OUTDIR, "dry_run_report.csv")
        with open(drp, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(dry[0].keys()) if dry else ["claim_id"])
            w.writeheader()
            w.writerows(dry)
        runnable = sum(1 for d in dry if d["runnable"])
        smi_ok = sum(1 for d in dry if d["smiles_resolved"])
        print(f"\nDRY RUN: {len(dry)} candidate claims")
        print(f"  ligand SMILES resolved: {smi_ok}/{len(dry)}   box parsed: {sum(1 for d in dry if d['box_parsed'])}")
        print(f"  receptor cached: {sum(1 for d in dry if d['receptor_cached'])}/{len(dry)}  (prep receptors into runner/receptors/<PDB>.pdbqt)")
        print(f"  RUNNABLE now (SMILES+box, pending receptor prep + compute): {runnable}/{len(dry)}")
        print(f"  env present at --bin: {env_ok}")
        print(f"  -> {drp}")
        return

    # append (resumable)
    exists = os.path.exists(out_csv)
    with open(out_csv, "a", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        if not exists:
            w.writeheader()
        w.writerows(new_rows)
    docked = [r for r in new_rows if r["status"] == "docked"]
    print(f"\nRe-executed {len(new_rows)} new claims ({len(docked)} docked) -> {out_csv}")
    if docked:
        print(f"  within 2 kcal/mol: {sum(r['within_2'] for r in docked)}/{len(docked)}")


if __name__ == "__main__":
    main()
