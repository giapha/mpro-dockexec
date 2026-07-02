# Reproduce Mpro-DockExec

All paths are relative to the repository root. Two levels of reproduction:
**(A)** regenerate every headline number from the released derived data (fast, no docking);
**(B)** re-run the actual AutoDock Vina docking from scratch (slow, needs the compute env).

## A. Regenerate the headline numbers (minutes, pure-Python)

```bash
# canonical executability distribution (deterministic rule classifier, human-aligned κ = 0.926)
python code/relock_rule_rerate.py
#   -> E1 47.9% (113) / E2 44.1% (104) / E3 8.1% (19) / E4 0%   (matches data/audit/stats_relocked.json)

# reporting-completeness + missing-field stats
python code/compute_stats.py

# inter-rater reliability
python code/compute_kappa.py
#   -> Cohen's κ = 0.926

# re-execution statistics from the locked outcomes
python code/runner/recompute_v2.py
#   -> median |Δ| 0.54 kcal/mol, 29/37 within 2.0; E3 0.24 (n=6) vs E2 0.59 (n=31); Mann–Whitney p = 0.14
```

Figures:
```bash
python code/render_figures.py          # executability distribution, missing-field matrix, re-execution scatter
Rscript code/render_fig1_ladder_Q1.R   # E0–E4 ladder (Q1 styling; needs R + ggplot2/patchwork)
Rscript code/render_fig5_reexec_Q1.R
```

## B. Re-run the docking from scratch (hours, needs Vina)

### 1. Build the environment
```bash
mamba env create -f environment.yml     # or micromamba / conda
mamba activate dock
python -c "import rdkit, vina; print('ok')"
vina --version                          # AutoDock Vina v1.2.7
# exact pins: docs/pip_freeze_pinned.txt
```

### 2. Runner order (offline-robust; deterministic: seed 200, exhaustiveness 16)
```bash
# resolve ligand structures to SMILES (PubChem; or seed offline from SDFs)
python code/runner/resolve_ligands_v3.py
# prepare each receptor (fetch PDB -> strip water/het -> meeko)
python code/runner/receptor_prep.py
# parse each paper's reported search box
python code/runner/parse_boxes.py
# dock + compare-to-reported + write per-claim provenance JSON
python code/runner/reexec_runner.py
# engine noise floor (3 seeds per ligand)
python code/runner/self_consistency.py
```
Each re-docked claim writes a provenance record (SMILES + source, box, seed, exhaustiveness, Vina version, command, hashes) so any single result is independently checkable.

### Notes & honest limitations
- **Search boxes** are span-parsed from text and not all human-verified; a wrong box can make Vina return no pose (a real finding, not a bug — reporting the box matters). Boxes wider than 40 Å (blind docking) are capped and flagged.
- **QC rule:** re-executed score > −2 kcal/mol (no bound pose) → excluded as a technical failure (3 excluded). A sensitivity analysis counting them as non-reproductions is in the manuscript (Table S5); the E3 < E2 ordering survives.
- **Copyright:** the 241 publisher full texts used for auditing are **not** in this repo. Retrieve them from their original open-access sources (PubMed Central) if you want to re-audit from raw text.
