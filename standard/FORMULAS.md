# Formal specification — executability classification & evaluation

The mathematical apparatus behind Mpro-DockExec. GitHub renders the `$…$` / `$$…$$` math below. This document defines exactly how a paper's 16 audited reporting-field states become an executability class (E0–E4), and the statistics used to evaluate the labels and the re-execution. Every symbol here is implemented in `code/` (`relock_rule_rerate.py`, `compute_kappa.py`, `compute_stats.py`, `runner/recompute_v2.py`) — if a coefficient here disagrees with the code, the code wins.

> **Scope.** This is the *verify / executability* axis — the object of this paper. A separate credibility-scoring axis (NSE quality/priority ranking) is developed in a companion benchmark study and is intentionally out of scope here.

---

## 0. Field-state primitive

For an audited field $f$, its reporting state $\mathrm{st}(f)\in\{\text{reported},\text{partial},\text{missing},\text{n/a}\}$ maps to a numeric value:

$$
s(f)=\begin{cases}
1.0 & \mathrm{st}(f)=\text{reported}\\
0.5 & \mathrm{st}(f)=\text{partial}\\
0.0 & \mathrm{st}(f)=\text{missing}\\
\varnothing\ (\text{not assessed}) & \text{empty / NA / unknown}
\end{cases}
$$

Not-assessed ($\varnothing$) values are **dropped from any denominator**, never treated as $0$.

The 16 MERS-Dock fields split into two tiers used below:

$$
\begin{aligned}
T_1 &= \{\text{pdb\_receptor},\ \text{grid\_center},\ \text{grid\_size},\ \text{docking\_software},\ \text{ligand\_identifier}\}\\
T_2 &= \{\text{software\_version},\ \text{search\_effort},\ \text{receptor\_prep},\ \text{ligand\_prep},\ \text{protonation},\ \text{water\_ion},\ \text{protein\_chain}\}
\end{aligned}
$$

---

## 1. Executability class $E(p)$

With the blocking and essential field sets

$$
\begin{aligned}
\text{BLOCK} &= \{\text{pdb\_receptor},\ \text{grid\_center},\ \text{docking\_software}\}\\
\text{ESS} &= \{\text{pdb\_receptor},\ \text{grid\_center},\ \text{grid\_size},\ \text{docking\_software},\ \text{software\_version},\ \text{receptor\_prep},\ \text{ligand\_prep}\}
\end{aligned}
$$

a paper $p$ is classified top-to-bottom, first matching branch wins:

$$
E(p)=\begin{cases}
E_1 & \exists\, f\in \text{BLOCK}:\ \mathrm{st}(f)=\text{missing}\\[4pt]
E_4 & \big(\forall f\in T_1\cup T_2:\ \mathrm{st}(f)=\text{reported}\big)\ \wedge\ \mathrm{st}(\text{seed})=\text{reported}\ \wedge\ \mathrm{st}(\text{code})=\text{reported}\\[4pt]
E_3 & \big(\forall f\in \text{ESS}:\ \mathrm{st}(f)=\text{reported}\big)\ \wedge\ \mathrm{st}(\text{ligand\_id})\in\{\text{reported},\text{partial}\}\\[4pt]
E_2 & \text{otherwise}
\end{cases}
$$

$E_0$ = no docking claim present. In words:

- **E1 — execution-blocked:** a Tier-1 foundational field (receptor, box centre, or software) is missing → you cannot even set up the run.
- **E2 — executable after assumptions:** runs only once you fill an under-reported field.
- **E3 — directly re-executable:** every essential input is present as reported.
- **E4 — fully reproducible:** E3 plus a disclosed random seed and reusable code/configuration.

$\text{BLOCK}$ and $\text{ESS}$ are the free parameters; they are **locked at the values that maximise agreement with the human reviewer**, $\kappa(E,\text{R1}) = 0.926$ (see §3). Applying this rule to the 236-paper corpus yields **E1 47.9 % / E2 44.1 % / E3 8.1 % / E4 0 %** — regenerate with `python code/relock_rule_rerate.py`.

---

## 2. Re-execution deviation & tolerance

For a re-docked claim $i$ with reported Vina score $r_i$ and re-executed score $\hat r_i$:

$$
\Delta_i = \hat r_i - r_i,\qquad \text{reported reproduces} \iff |\Delta_i|\le \tau .
$$

The tolerance $\tau$ is **noise-calibrated**, not arbitrary. Each of $n_s$ curated ligands is re-docked across three seeds; its within-ligand score range is $\rho_\ell=\max_k \hat r_{\ell k}-\min_k \hat r_{\ell k}$. The engine noise floor is the median range (0.04 kcal/mol; max 0.38), and

$$
\tau=\max\!\big(2.0,\ P_{95}(\{\rho_\ell\})\big)=2.0\ \text{kcal/mol}.
$$

A claim is a **technical failure** (excluded from the reproduction denominator) if $\hat r_i > -2$ kcal/mol, i.e. Vina returned no bound pose. Reported per stratum:

$$
\widetilde{|\Delta|}_{E}= \operatorname{median}\{|\Delta_i| : E(p_i)=E\},\qquad
\text{within-}\tau_E = \frac{\#\{i: E(p_i)=E,\ |\Delta_i|\le\tau\}}{\#\{i:E(p_i)=E\}} .
$$

Result: $\widetilde{|\Delta|}_{\text{all}}=0.54$ (29/37 within $\tau$); $\widetilde{|\Delta|}_{E3}=0.24$ (n = 6) vs $\widetilde{|\Delta|}_{E2}=0.59$ (n = 31).

---

## 3. Evaluation statistics

**Cohen's $\kappa$** — inter-rater reliability of the executability labels (two human reviewers; reproduced by the rule classifier and a blind LLM rater):

$$
\kappa=\frac{p_o-p_e}{1-p_e},\qquad
p_o=\tfrac1n\textstyle\sum_i \mathbb{1}[a_i=b_i],\qquad
p_e=\textstyle\sum_c \hat p_a(c)\,\hat p_b(c).
$$

Observed $\kappa = 0.926$ (raw agreement 0.97; a single borderline disagreement on paper P0005).

**Wilson 95 % interval** — for every reported proportion (e.g. each E-class share):

$$
\frac{\hat p+\frac{z^2}{2n}\ \pm\ z\sqrt{\hat p(1-\hat p)/n+z^2/4n^2}}{1+z^2/n},\qquad z=1.96 .
$$

**Mann–Whitney $U$** — tests whether the E3 and E2 deviation distributions differ (used on $\{|\Delta_i|\}$):

$$
U=\min(U_1,U_2),\quad U_1=R_1-\tfrac{n_1(n_1+1)}{2},
$$

with $R_1$ the rank-sum of group 1 and a normal approximation for the two-sided $p$. Observed $p = 0.14$ (E3 stratum $n = 6$) → the E3-below-E2 ordering is a **directional** signal, not a powered effect.

**Executability AUROC** — area under the ROC of any ranker's score against the binary label $\mathbb{1}[E\ge E_2]$ (broad) or $\mathbb{1}[E\ge E_3]$ (strict).

---

## 4. What is locked vs. tunable

| Symbol | Role | Status |
|---|---|---|
| $\text{BLOCK},\ \text{ESS}$ | E-class decision rule | **locked** at max-$\kappa$ vs human R1 ($=0.926$) |
| $\tau=2.0$ | reproduction tolerance | **locked** = $\max(2.0, P_{95}$ engine noise$)$, pre-specified before scoring |
| technical-failure cut $-2$ | no-pose QC | **locked**; sensitivity analysis counting failures as non-reproductions preserves E3 < E2 |
| $s(f)$ mapping | field-state value | fixed (1 / 0.5 / 0) |

*Source of truth: the scripts in `code/`. Regenerate this document's numbers with `relock_rule_rerate.py` + `runner/recompute_v2.py`.*
