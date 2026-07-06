# Mpro-DockExec

**A reporting-completeness and re-executability audit of the open-access SARS-CoV-2 main-protease (Mpro) molecular-docking literature — with the reporting standard, the audit dataset, and the re-execution scripts that regenerate every headline number.**

> A docking score is the output of a workflow, not a standalone fact: it depends on the receptor, the ligand, the software, the search box, the random seed, and several preparation choices. Report the score without the workflow and the result cannot be re-run. This repository measures how often that happens — and ships everything needed to check the measurement itself.

This repository is itself the reproducibility artifact for the study. It practises what the paper argues: the field-state data plus a deterministic classifier plus the analysis scripts regenerate the paper's headline figures from a single command.

---

## Headline findings (N = 236 open-access Mpro docking papers)

| Executability class | What it means | Share |
|---|---|---|
| **E4** — fully reproducible | disclosed seed + reusable configuration | **0 / 236 (0%)** |
| **E3** — directly re-executable | all foundational inputs present as reported | **8.1%** (95% CI 5.2–12.2) |
| **E2** — executable after assumptions | runs only once you fill an under-reported field | **44.1%** |
| **E1** — execution-blocked | a foundational field is missing | **47.9%** |

- The **search-box centre** — the single most consequential missing field — is cleanly reported in only about **one-third** of papers.
- Two independent human reviewers agree on the labels at **Cohen's κ = 0.926**, reproduced at the same value by a deterministic codebook classifier and a blind language-model rater.
- **Re-execution (37 QC'd claims, 2 targets, AutoDock Vina 1.2.7):** against the engine's own near-deterministic run-to-run noise (within-ligand range median **0.04 kcal/mol**), reported scores reproduce to a **median of 0.54 kcal/mol** (29/37 within a 2.0 kcal/mol noise-calibrated tolerance). Directly-executable (E3) claims reproduce essentially at the noise floor (**0.24**, n = 6); assumption-dependent (E2) claims about twofold further (**0.59**, n = 31). The E3 stratum is small and the difference is **not statistically significant (Mann–Whitney p = 0.14)** — we report it as a *directional* signal, not a powered effect.

Because the corpus is open-access and text-extractable, these figures likely **overestimate** executability in the broader, paywalled literature.

---

## What's in here

```
standard/     MERS-Dock reporting standard (16 fields) + E0–E4 ladder + FORMULAS.md (formal spec) + extraction schema
data/audit/   Per-paper 16-field reporting states (N=236) + deep span-verified subset (N=33) + locked stats
data/reexecution/  Re-docking outcomes, ligand provenance (PubChem CID + InChIKey), Vina self-consistency, reported boxes
code/         The deterministic re-lock classifier, stats, κ, and figure scripts
code/runner/  The re-execution engine: claim → AutoDock Vina → compare-to-reported → per-claim provenance JSON
figures/      Publication figures (executability distribution, missing-field matrix, re-execution scatter, PRISMA)
manuscript/   Abstract + preprint pointer (link added on posting)
docs/         Full reproduction guide + pinned environment
```

Every number in the paper traces to a file here. Nothing is eyeballed off a plot.

## Reproduce the headline in three commands

```bash
# 1. Build the pinned environment (AutoDock Vina 1.2.7, RDKit, meeko)
mamba env create -f environment.yml && mamba activate dock

# 2. Regenerate the executability distribution from the raw 16-field states
#    (deterministic rule classifier, human-aligned at κ = 0.926)
python code/relock_rule_rerate.py            # -> E1 47.9 / E2 44.1 / E3 8.1 / E4 0

# 3. Recompute the re-execution statistics from the locked outcomes
python code/runner/recompute_v2.py           # -> median |Δ| 0.54, 29/37 within 2.0; E3 0.24 vs E2 0.59
```

Re-running the docking itself (optional, GPU/CPU-heavy) uses `code/runner/` — see [`docs/REPRODUCE.md`](docs/REPRODUCE.md).

## The reusable part: the MERS-Dock reporting standard

`standard/MERS-Dock_Reporting_Guideline_v1.md` is a **16-field checklist** for reporting a docking result so that someone else can re-run it. It is tiered:

- **Tier 1 (blocks execution if missing):** PDB/receptor, search-box centre, docking software.
- **Tier 2 (forces an assumption):** box size, ligand identity, software version, receptor/ligand preparation, …
- **Tier 3 (robustness):** random seed, validation re-docking, code artifacts.

Authors can adopt it as a submission checklist; reviewers can score against it; tools can extract against it. It is released here independently of the audit so it can be reused.

**The formal specification** — how the 16 field states become an E0–E4 class, and every statistic used (Cohen's κ, Wilson intervals, the noise-calibrated re-execution tolerance, Mann–Whitney) — is written out as rendered math in [`standard/FORMULAS.md`](standard/FORMULAS.md). The decision rule there is exactly what `code/relock_rule_rerate.py` runs, locked at the value that maximises agreement with the human reviewer (κ = 0.926).

## Data provenance & copyright

The audit was performed on **241 open-access full texts** retrieved from PubMed Central. Those publisher texts are **not redistributable and are not included here.** This repository ships only:

- **derived** data: executability labels, the 16 reporting-field states, missing-field frequencies, re-execution outcomes;
- the reporting standard and extraction schema;
- the analysis and re-execution **code**;
- the figures.

Short verbatim spans used as evidence during auditing are **omitted** from the public field-state tables (`reporting_field_states_N33_spanfree.csv` has the `span` column stripped). See [`data/README.md`](data/README.md) and [`data/DATASHEET.md`](data/DATASHEET.md).

## Manuscript

Preprint: *"Measuring the re-executability of a computational claim: a deterministic reporting standard and a noise-calibrated re-execution protocol for molecular docking"* — **preprint forthcoming** (link and DOI added here on posting). Abstract in [`manuscript/README.md`](manuscript/README.md).

## Citation

If you use the standard, the dataset, or the code, please cite the preprint (see [`CITATION.cff`](CITATION.cff); a Zenodo DOI is minted on first release). Until the preprint is live, cite this repository directly.

## Authors

Vincent He¹ (corresponding, Vincentgiap@gmail.com) · Eric Wang¹ · Cris Nguyen¹
¹ NewScience Lab

## License

- **Code** (`code/`, `standard/` schema, scripts): [MIT](LICENSE).
- **Data & figures** (`data/`, `figures/`) and the MERS-Dock standard text: [CC BY 4.0](LICENSE-DATA.md).

---

*Competing-interest note: the authors are affiliated with NewScience Lab, which develops verification- and executability-aware tools for computational scientific claims. The apparatus is named generically, the platform is not a study object, and all data, code, and the reporting standard are released openly so the findings can be assessed independently of any commercial interest.*
