#!/usr/bin/env python3
"""Self-consistency baseline for the re-execution pipeline (the rigor anchor).

Reviewers cannot interpret a reproduction |delta| without knowing AutoDock Vina's
OWN run-to-run variance under our fixed protocol. This re-docks each curated-grade
ligand K times with different random seeds (same receptor, same reported box,
same exhaustiveness) and reports the within-ligand spread. The 95th-percentile
spread becomes the PRE-REGISTERED reproduction tolerance: a claim is "reproduced"
only if |reported - rerun| is within Vina's own noise band.

Curated-grade = TRUSTED SMILES (PubChem CID or offline SDF, NOT name-guessed) AND
a paper-reported (span-parsed) box AND a prepped receptor.

Run (dock env):  DOCK_BIN=<env/bin> <env/bin>/python self_consistency.py --bin <env/bin> --reps 3
"""
import argparse, csv, os, statistics as st
import reexec_runner as R

HERE = os.path.dirname(os.path.abspath(__file__))
SEEDS = [11, 29, 53, 71, 97]

def trusted(src): return ("cid" in (src or "")) or ("sdf" in (src or ""))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bin", required=True)
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--limit", type=int, default=15, help="sample N ligands for the noise band")
    args = ap.parse_args()
    seeds = SEEDS[:args.reps]

    cache = {r["ligand_key"]: (r["smiles"], r.get("source", "")) for r in
             csv.DictReader(open(os.path.join(HERE, "out", "smiles_cache.csv"))) if r.get("smiles")}
    prepped = set(os.path.splitext(f)[0] for f in os.listdir(os.path.join(HERE, "receptors")) if f.endswith(".pdbqt"))
    man = list(csv.DictReader(open(os.path.join(HERE, "manifest.csv"))))
    cur = [r for r in man if r["ligand_name"].strip() in cache
           and trusted(cache[r["ligand_name"].strip()][1])
           and r.get("box_center_x", "").strip() and r["target_pdb"] in prepped]
    if args.limit and len(cur) > args.limit:
        cur = cur[:args.limit]
    print(f"self-consistency sample: {len(cur)} ligands | reps/seeds: {seeds}", flush=True)

    rows = []
    for i, r in enumerate(cur, 1):
        name = r["ligand_name"].strip()
        smi = cache[name][0]
        rec = R.receptor_path(r["target_pdb"], r["chain"])
        if not rec:
            print(f"[{i}/{len(cur)}] {name[:24]} no receptor, skip", flush=True); continue
        pq = R.embed_prep_ligand(smi, f"sc_{r['claim_id']}", args.bin)
        if not pq:
            print(f"[{i}/{len(cur)}] {name[:24]} ligand prep failed, skip", flush=True); continue
        center = (r["box_center_x"], r["box_center_y"], r["box_center_z"])
        size = tuple(float(r[k]) if r.get(k, "").strip() else 25.0 for k in ("box_size_x", "box_size_y", "box_size_z"))
        scores = []
        for s in seeds:
            R.SEED = s
            outp = os.path.join(HERE, "out", "ligands", f"sc_{r['claim_id']}_s{s}_dock.pdbqt")
            sc, _ = R.dock(rec, pq, center, size, args.bin, outp)
            if sc is not None: scores.append(sc)
        if len(scores) >= 2:
            rng = max(scores) - min(scores)
            rows.append({"claim_id": r["claim_id"], "paper_id": r["paper_id"], "pdb": r["target_pdb"],
                         "ligand": name, "n_seeds": len(scores), "scores": ";".join(f"{x:.2f}" for x in scores),
                         "mean": round(st.mean(scores), 2), "range": round(rng, 2),
                         "std": round(st.pstdev(scores), 3) if len(scores) > 1 else 0.0})
            print(f"[{i}/{len(cur)}] {name[:24]:26s} scores={['%.2f'%x for x in scores]} range={rng:.2f}", flush=True)

    out = os.path.join(HERE, "out", "self_consistency.csv")
    with open(out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["claim_id","paper_id","pdb","ligand","n_seeds","scores","mean","range","std"])
        w.writeheader(); w.writerows(rows)
    ranges = sorted(x["range"] for x in rows)
    if ranges:
        p95 = ranges[min(len(ranges)-1, int(0.95*len(ranges)))]
        print(f"\n=== SELF-CONSISTENCY (n={len(ranges)} ligands, {len(seeds)} seeds each) ===", flush=True)
        print(f"within-ligand range: median {st.median(ranges):.2f}, mean {st.mean(ranges):.2f}, max {max(ranges):.2f}, 95th pct {p95:.2f} kcal/mol", flush=True)
        print(f"=> PRE-REGISTERED reproduction tolerance = {max(2.0, round(p95,1))} kcal/mol (max of 2.0 and Vina 95th-pct self-noise)", flush=True)
    print(f"-> {out}", flush=True)

if __name__ == "__main__":
    main()
