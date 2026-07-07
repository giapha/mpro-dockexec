# Changelog

All notable changes to Mpro-DockExec are recorded here. Versions follow the Zenodo release tags.

## [0.1.0] — 2026-07-03 (initial public release)
- MERS-Dock reporting standard v1 (16 fields, E0–E4 ladder) + extraction schema.
- Reporting audit of **236** open-access Mpro docking papers (per-paper 16-field states + human-aligned executability labels; canonical distribution E1 47.9 / E2 44.1 / E3 8.1 / E4 0).
- Deep span-verified subset (**33** papers) + missing-field frequencies.
- Re-execution of **37** QC'd claims across 2 targets (AutoDock Vina 1.2.7): median |Δ| 0.54 kcal/mol, 29/37 within a 2.0 noise-calibrated tolerance; E3 0.24 vs E2 0.59 (directional, p = 0.14).
- Deterministic re-lock classifier, stats, κ, and figure scripts; pinned `environment.yml`.
- Datasheet, data dictionary, CITATION.cff, Zenodo metadata.
- Copyright firewall: publisher full texts excluded; evidence spans stripped from public tables.

### v0.1.1 — 2026-07-07 (re-execution powered + reframed)
- Re-execution extended to **48** QC'd claims (3 targets). Headline is **box-size availability**: reported box 0.33 vs defaulted 0.91, significant (Mann–Whitney p = 0.024).
- Executability label reframed as an **executability gate** (which claims can be re-executed at all), not a reproducibility predictor; re-execution demoted to a bounded proof of concept. Figure re-rendered by box availability.

### Pending
- Preprint link + DOI (OSF/arXiv; added on posting).
- Zenodo concept DOI (minted on first archived release).
- Human-verification pass on span-parsed search boxes (documented limitation).
