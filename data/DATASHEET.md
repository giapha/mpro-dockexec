# Datasheet — Mpro-DockExec

Following *Datasheets for Datasets* (Gebru et al., 2021). Short-form; the manuscript Methods and Supplementary carry the full protocol.

## Motivation
- **Purpose.** Measure how re-executable published SARS-CoV-2 Mpro molecular-docking results are, against an explicit 16-field reporting standard (MERS-Dock) and a five-level executability ladder (E0–E4); and validate the labels by re-docking a subset.
- **Created by.** NewScience Lab (V. He, E. Wang, C. Nguyen).

## Composition
- **Instances.** (a) 236 open-access Mpro docking papers, each scored on 16 reporting fields → an executability class; (b) a 33-paper subset with span-verified field states; (c) 37 quality-controlled ligand-level claims re-docked with AutoDock Vina.
- **What each instance contains.** Field-completeness states (`reported`/`partial`/`missing`), the derived executability class, and — for the re-execution set — reported vs re-executed docking scores, ligand identity (PubChem CID + InChIKey), and the search box used.
- **Does it contain raw article text?** **No.** Only derived states and short structured values. Verbatim evidence spans are held privately; the public field-state tables have the span column stripped.
- **Sampling.** Corpus: 1,400 raw records → 1,018 de-duplicated → dual-AI screening → open-access full text retrievable → confirmed original Mpro docking studies. See `figures/FigS1_PRISMA_flow.png`.

## Collection process
- **How.** Records screened by a dual-model pipeline; full texts retrieved from PubMed Central; each paper audited field-by-field with source-span anchoring; a 33-paper subset countersigned by a second human. Re-execution: ligands resolved to PubChem CIDs, receptors prepared with meeko, docked with AutoDock Vina 1.2.7 (RDKit ETKDGv3, seed 200, exhaustiveness 16).
- **Timeframe.** Corpus and audit locked June 2026.

## Preprocessing / labeling
- **Executability labels** assigned by a deterministic codebook classifier and reconciled to human review. Inter-rater reliability κ = 0.926 (two humans), reproduced by the rule classifier and a blind LLM rater.
- **Re-lock.** The canonical labels come from `relock_rule_rerate.py`; an earlier optimistic pipeline labeling is retained only for provenance.

## Uses
- **Intended.** Meta-research on computational reproducibility; a benchmark/measurement layer for automated verification of docking claims; a submission/review checklist (the MERS-Dock standard).
- **Out of scope.** Judging the *scientific correctness* of any individual paper's biology. E-class measures **re-executability of the reported workflow**, not whether the drug target claim is true. A high-E paper can be wrong; a low-E paper can be right but under-reported.

## Distribution & maintenance
- **License.** Data & figures CC BY 4.0; code MIT.
- **Copyright limit.** Publisher full texts are not included and must be obtained from the original open-access sources.
- **Versioning.** Released with a Zenodo DOI; corrections tracked in `CHANGELOG.md`.
- **Contact.** Vincentgiap@gmail.com.

## Known limitations
- Open-access-only corpus → likely **overestimates** executability of the whole (incl. paywalled) literature.
- Re-execution E3 stratum is small (n = 6); the E3-vs-E2 gap is directional, not statistically significant (p = 0.14).
- Search boxes are span-parsed and not all individually human-verified.
