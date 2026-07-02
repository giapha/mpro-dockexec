# Data dictionary — Mpro-DockExec

All tables are **derived** from open-access full texts. Raw publisher texts are not redistributed (see copyright note in the top-level README and the datasheet). Every value regenerates from the scripts in `code/`.

## `audit/` — reporting-completeness audit

### `paper_audit_N236_field_states.csv` — the headline dataset (N = 236)
One row per eligible Mpro docking paper. The 16 MERS-Dock fields are scored `reported` / `partial` / `missing`.

| column | meaning |
|---|---|
| `paper_idx` | anonymised paper index within the locked corpus |
| `target_pdb` | receptor PDB ID as reported (blank if not given) |
| `software` | docking software as reported |
| `paper_e_class` | pipeline-assigned executability class (**superseded** — see note) |
| `blocking_field` | the first Tier-1 field that blocks execution, if any |
| `n_ligand_claims` | number of ligand-level docking claims in the paper |
| `pdb_receptor … numeric_result` | the 16 reporting-field states |

> **Which E-class is canonical?** The paper reports the **human-aligned re-lock**, not the `paper_e_class` column. Run `python code/relock_rule_rerate.py` to regenerate the canonical labels (deterministic rule classifier, agreeing with human reviewer R1 at κ = 0.926). The pipeline's original `paper_e_class` was an optimistic outlier (κ = 0.075 vs R1) and is kept only for transparency. Canonical distribution → `stats_relocked.json`.

### `deep_audit_N33_span_verified.csv` — countersigned deep subset (N = 33)
The papers whose 16 fields were **span-verified against the full text** (each state anchored to a located passage during the private audit). The public table keeps only derived states and labels: `final_E_class`, per-field `*_span_verified` counts, and integrity/consistency flags. Verbatim spans, access-route notes, and free-text adjudication rationales are omitted for copyright safety. This is the high-confidence core; the N = 236 table is the scaled reporting audit.

### `reporting_field_states_N33_spanfree.csv`
Long-format `(paper_id, field, state, span_verified, original_state)` for the deep subset. The verbatim `span` column has been **stripped** for copyright safety; states remain fully auditable.

### `missing_parameter_frequency_N33.csv`
Per-field `n_reported / n_partial / n_missing / pct_missing`. This is the source of the "which fields go missing" figure. `random_seed` (93.9% missing) and `code_artifacts` (90.9%) top the list; `docking_software` and `numeric_result` are always present (by construction — a docking paper reports a score).

### `stats_relocked.json` (canonical) / `stats_pipeline_superseded.json`
Locked executability distributions with Wilson 95% CIs. **Use `stats_relocked.json`** — it matches the manuscript (E1 47.9 / E2 44.1 / E3 8.1 / E4 0). The `_superseded` file is the pre-relock pipeline output, retained for provenance.

## `reexecution/` — re-docking validation (N = 37 QC'd claims)

### `reproduction_outcomes.csv`
One row per re-docked claim: reported score, re-executed Vina score, absolute deviation, executability class, target, ligand. QC rule: docks with re-executed score > −2 kcal/mol (no bound pose) are excluded as technical failures (3 excluded; see `reproduction_LOCKED.json`).

### `ligand_provenance.csv`
Every re-docked ligand anchored to a **PubChem CID + InChIKey**, with the resolved SMILES and its source. This is what makes the re-execution checkable rather than asserted.

### `self_consistency.csv`
Each of 15 curated ligands re-docked across three random seeds. The within-ligand score range defines the engine's run-to-run **noise floor** (median 0.04, max 0.38 kcal/mol); its 95th percentile sets the 2.0 kcal/mol reproduction tolerance. **Reproduction is judged against noise, not against an arbitrary threshold.**

### `box_table.csv`
The search box (centre + size) parsed from each paper's text and used in re-execution. Blind-docking boxes wider than 40 Å are capped (flagged); span-parsed values are not individually human-verified — a documented limitation.

### `reproduction_LOCKED.json` / `reproduction_v2_stats.json`
The frozen re-execution result (N, medians, CIs, Mann–Whitney p, by-target breakdown). `recompute_v2.py` regenerates these from `reproduction_outcomes.csv`.

## Honesty notes carried from the analysis
- The E3-vs-E2 difference is **not significant** (Mann–Whitney p = 0.14, n_E3 = 6). Reported as directional; significance was **not** forced.
- V2 uses each paper's **reported** box; an earlier V1 used a default 25 Å box. Switching to reported boxes tightened both strata (see `figures/FigS2_method_fix.png`), showing part of the V1 spread was a default-box artifact.
- Sensitivity analysis counting the 3 failed-to-bind docks as non-reproductions preserves the E3 < E2 ordering (see manuscript Table S5).
