# MERS-Dock: Minimum Executable Reporting Set for Molecular Docking (v1)

**A reporting guideline derived from a source-verified executability audit of SARS-CoV-2 Mpro docking literature (N=33 papers, 283 claims).**

> Purpose: give authors, reviewers, and editors a concrete, field-tested checklist so that a published docking claim can be **re-executed** from the reported record. Each item states *what to report*, *why it gates re-execution*, *how often it was actually reported in our audit*, and *which executability class (E0–E4)* it controls. This is the reporting-standard analogue of CONSORT/ARRIVE/PRISMA for protein–ligand docking.

## How to use
- **Authors:** report every Tier-1 item explicitly; deposit a machine-readable config (Tier-3) to reach E4.
- **Reviewers/editors:** treat missing Tier-1 items as a revision request, not a stylistic preference.
- **Auditors / automated systems:** each item maps to a structured field with a required source span (verbatim quote), enabling source-verified extraction.

Executability ladder (outcome the checklist predicts):
**E0** not extractable · **E1** extractable but execution-blocked (a Tier-1 input missing) · **E2** executable only with explicit assumptions (Tier-1 complete, Tier-2 gaps) · **E3** executable as reported (Tier-1+2 complete) · **E4** executable + robustness-ready (Tier-3 artifacts + seed shared).

---

## Tier 1 — Execution-blocking (absence ⇒ E1; the run cannot be constructed)

| # | Report | Why it gates re-execution | Audited reporting rate |
|---|---|---|---|
| 1 | **Receptor identity** — PDB ID (or model source + method) | No structure ⇒ no run | 94% reported |
| 2 | **Search-box centre** — x,y,z of the grid/site centre | Defines *where* docking happens; the most common silent blocker | 42% reported |
| 3 | **Search-box size** — dimensions or radius (+ spacing for grid methods) | Defines the searched volume; defaults are tool-specific | 36% reported |
| 4 | **Docking software** — program name | Determines algorithm + scoring | 100% reported |
| 5 | **Ligand identity** — unambiguous ID (InChIKey / PubChem CID / SMILES), not just a common name | A name alone is not resolvable to one structure | 27% explicit ID (88% any identifier-or-name) |

*Audit finding:* search-box centre/size were the dominant cause of E1 — papers reported a score but not where the box sat (e.g., "80×80×80 grid" with no centre). **Report the centre coordinates, always.**

## Tier 2 — Assumption-forcing (absence ⇒ E2; runnable only by guessing)

| # | Report | Why it matters | Audited reporting rate |
|---|---|---|---|
| 6 | **Software version** (+ build) | Scoring/algorithm changed across versions | 52% |
| 7 | **Scoring function / mode** | Different scoring ⇒ different ranking | (add as scored field) |
| 8 | **Search effort** — exhaustiveness / GA runs / num modes | Controls sampling depth & stochastic spread | 39% |
| 9 | **Receptor preparation** — protonation, charges, H-addition, tool | Changes the energy surface | 76% |
| 10 | **Ligand preparation** — 3D generation, charges, tool | Changes the conformer pool | 73% |
| 11 | **Protonation / tautomer state** of ligand (and key catalytic residues) | Mpro His41/Cys145 protonation strongly affects binding | 0% explicit (52% partial) |
| 12 | **Water / ion / cofactor handling** | Retained waters change the pocket | 42% |
| 13 | **Protein chain / oligomeric state** | Wrong chain ⇒ wrong pocket | 15% |

*Audit finding:* protonation/tautomer state was **never** stated explicitly — a Tier-2 systemic gap. Naming the His41/Cys145 dyad protonation is the single cheapest E2→E3 upgrade for Mpro.

## Tier 3 — Robustness & exact reproducibility (presence ⇒ E4)

| # | Report | Why it matters | Audited reporting rate |
|---|---|---|---|
| 14 | **Random seed / determinism policy** | Stochastic docking is run-to-run variable without it | 3% |
| 15 | **Validation / redocking** — native-ligand RMSD or equivalent | Evidence the protocol recovers a known pose | 30% |
| 16 | **Reusable artifacts** — config file, input/output structures, code (DOI/repo) | Enables exact, audited re-execution | 0% explicit (9% any mention) |

*Audit finding:* **no paper reached E4.** Not one combined a disclosed seed with shared configuration artifacts. A single deposited config file + seed would move most E2/E3 papers to E4 at negligible cost.

---

## Minimal deposit that yields E4
A one-file machine-readable config (e.g., the Vina/AutoDock config: receptor PDBQT reference, box centre+size, exhaustiveness, seed, num_modes) + ligand SMILES/InChIKey list + the prepared receptor/ligand files, deposited with a DOI. With these, an independent party (or an automated verification engine) can re-execute the exact run and compute a reproducibility score.

## Empirical basis & honest scope
Rates above are span-verified AI-candidate values from 33 open-access Mpro docking papers (pending two-reviewer human countersignature). They quantify **documentation completeness**, not methodological quality or biological validity. The checklist generalizes by construction (the fields are engine-agnostic), but the prevalence figures are specific to this corpus.

*MERS-Dock v1 — companion artifact to "How Executable Are Published Molecular Docking Claims?" Versioned; community feedback expected to refine field definitions and add engine-specific annexes (Vina/GOLD/Glide/DockThor).*
