# Arm B re-execution runner — status & workflow

The flagship's reproducibility engine: takes executable docking claims → re-runs AutoDock Vina → compares to the reported score → reproduction outcome + provenance. Built + **demonstrated end-to-end on real Vina v1.2.7** (not a stub).

## Honest state (2026-06-28)
- **Engine works.** P0006 (6LU7) re-ran cleanly: **3/4 within 2 kcal/mol, median |Δ| 0.539** (matches Paper 1's hand-run reproduction). Full provenance per claim (`out/provenance/*.json`: SMILES+source, box, seed, exhaustiveness, Vina version, command, hashes).
- **Manifest:** 145 executable claims; 44 ready-to-dock (box parsed) across 3 dockable PDBs.
- **Scale-up is INFRA/HUMAN-gated, not code-gated:**
  - `smiles_unresolved` (34) — **PubChem throttled/down** this session (we hit it ~120×). Retry in a fresh network window, or seed offline (below).
  - `needs_prepped_receptor:6yb7` (1+) — **RCSB + EBI blocked** from this sandbox (only OpenAlex/PubChem are allowlisted); can't fetch new PDB structures now.
  - `dock_failed_no_pose` (5, P0014) — **auto-parsed box centers are unreliable**: P0014's span-parsed box did not fit the 6LU7 receptor → Vina returned no pose. This is the R7 lesson made concrete and a genuine paper finding (reporting/box specification matters). **Box centers MUST be human-verified, and ideally each paper gets its own receptor prep, before reruns count as scientific evidence.**

## Files / workflow
```
build_manifest.py        audit data -> manifest.csv (executable claims + parsed boxes)
resolve_smiles.py        SYSTEM python3 (working TLS): PubChem -> out/smiles_cache.csv
seed_smiles_from_sdf.py  OFFLINE fallback (dock-env rdkit): SMILES from Paper-1 SDFs -> cache
receptor_prep.py         fetch PDB -> strip water/het -> meeko mk_prepare_receptor -> receptors/<PDB>.pdbqt
reexec_runner.py         dock + compare + provenance (reads smiles_cache + receptors). --dry-run testable offline.
```
Run order (offline-robust): `resolve_smiles.py` (system) **or** `seed_smiles_from_sdf.py` (dock env) → `receptor_prep.py` (dock env) → `/tmp/mm/envs/dock/bin/python reexec_runner.py`. Resumable; deterministic (seed 200, exhaustiveness 16).

## To reach full Arm B (flagship)
1. Human-verify span-parsed box centers in `manifest.csv` (R7) — or re-extract per paper. **Highest-value correctness step.**
2. Per-paper receptor prep (not one shared 6LU7) for the dockable papers.
3. Fresh PubChem window for SMILES of the remaining ligands (or expand offline SDF seeding).
4. Fetch 6Y2E / 6yb7 PDBs when RCSB is reachable → prep → run.
Target N: 20–40 reruns across topics. Pilot already has Paper 1's 26 + this engine to scale.
