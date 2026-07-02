#!/usr/bin/env python3
"""
Reliability metrics for the executability audit. Stdlib only.

Two distinct things, never conflated:
  (A) AUTOMATED concordance = candidate E-class vs adversarial-adjudicated E-class.
      The adjudicator SAW the candidate, so this is a CORRECTION RATE / concordance,
      NOT an independent inter-rater kappa. Reported honestly as such.
  (B) HUMAN inter-rater kappa = two INDEPENDENT human reviewers (Reviewer 1, Reviewer 2)
      filling R1_E_class / R2_E_class in countersign_paper_queue.csv, blind to each other.
      Cohen's kappa + linear/quadratic weighted kappa + raw agreement + protocol >=0.70 gate.
      This is the protocol's primary reliability metric and CANNOT be produced by AI.

Run after humans fill the queue: python3 compute_kappa.py
"""
import csv, os, json
HERE=os.path.dirname(os.path.abspath(__file__)); PKG=os.path.join(HERE,"..")
ORDER=["E0","E1","E2","E3","E4"]; IDX={e:i for i,e in enumerate(ORDER)}

def confusion(pairs):
    n=len(ORDER); M=[[0]*n for _ in range(n)]
    for a,b in pairs:
        if a in IDX and b in IDX: M[IDX[a]][IDX[b]]+=1
    return M

def kappas(pairs):
    pairs=[(a,b) for a,b in pairs if a in IDX and b in IDX]
    N=len(pairs)
    if N==0: return None
    M=confusion(pairs); n=len(ORDER)
    po=sum(M[i][i] for i in range(n))/N
    r=[sum(M[i])/N for i in range(n)]; c=[sum(M[i][j] for i in range(n))/N for j in range(n)]
    pe=sum(r[i]*c[i] for i in range(n))
    cohen=(po-pe)/(1-pe) if pe<1 else 1.0
    def wkappa(power):
        wsum=0; esum=0
        for i in range(n):
            for j in range(n):
                w=1-(abs(i-j)/(n-1))**power
                wsum+=w*M[i][j]/N
                esum+=w*r[i]*c[j]
        return (wsum-esum)/(1-esum) if esum<1 else 1.0
    return {"N":N,"raw_agreement":round(po,3),"cohen_kappa":round(cohen,3),
            "linear_weighted_kappa":round(wkappa(1),3),"quadratic_weighted_kappa":round(wkappa(2),3)}

# (A) automated concordance: candidate vs adjudicated
papers=list(csv.DictReader(open(os.path.join(PKG,"data","method_audit_candidate.csv"),encoding="utf-8")))
auto_pairs=[(p["candidate_E_class"],p["final_E_class"]) for p in papers if p.get("candidate_E_class") and p.get("final_E_class")]
changed=sum(1 for a,b in auto_pairs if a!=b)
auto={"metric":"AI candidate vs adversarial-adjudicated E-class (concordance / correction rate, NOT independent kappa)",
      "n_papers":len(auto_pairs),"unchanged":len(auto_pairs)-changed,"changed_by_adjudication":changed,
      "correction_rate":round(changed/len(auto_pairs),3),"raw_concordance":round((len(auto_pairs)-changed)/len(auto_pairs),3)}

# (B) human kappa from countersign queue (if filled)
human={"status":"PENDING — countersign_paper_queue.csv R1_E_class/R2_E_class empty"}
qf=os.path.join(PKG,"countersign_paper_queue.csv")
if os.path.exists(qf):
    q=list(csv.DictReader(open(qf,encoding="utf-8")))
    hp=[(r.get("R1_E_class","").strip(),r.get("R2_E_class","").strip()) for r in q
        if r.get("R1_E_class","").strip() and r.get("R2_E_class","").strip()]
    if hp:
        k=kappas(hp)
        human={"status":"COMPUTED","metric":"independent human Reviewer-1 vs Reviewer-2 E0-E4","n_double_reviewed":len(hp),
               **k,"protocol_gate_0.70_passed": (k["quadratic_weighted_kappa"]>=0.70)}

out={"automated_concordance":auto,"human_inter_rater_kappa":human}
json.dump(out,open(os.path.join(HERE,"reliability.json"),"w"),indent=1)
print(json.dumps(out,indent=1))

# Table 5 markdown
L=["# Table 5 — Reliability\n",
   "## (A) Automated pipeline concordance (reported as correction rate, not independent κ)",
   f"- Adversarial adjudication changed the candidate E-class in {auto['changed_by_adjudication']}/{auto['n_papers']} papers "
   f"(correction rate {100*auto['correction_rate']:.1f}%; raw concordance {100*auto['raw_concordance']:.1f}%).",
   "\n## (B) Independent human inter-rater κ (PROTOCOL PRIMARY — pending human countersignature)"]
if human["status"]=="COMPUTED":
    L.append(f"- N double-reviewed = {human['n_double_reviewed']}; raw agreement {human['raw_agreement']}; "
             f"Cohen's κ {human['cohen_kappa']}; linear-weighted κ {human['linear_weighted_kappa']}; "
             f"quadratic-weighted κ {human['quadratic_weighted_kappa']}; protocol ≥0.70 gate "
             f"{'PASSED' if human['protocol_gate_0.70_passed'] else 'NOT met → revise codebook + re-annotate'}.")
else:
    L.append("- [PENDING-κ] Two independent reviewers must fill R1_E_class / R2_E_class (blind) in "
             "`countersign_paper_queue.csv`; rerun `compute_kappa.py` to populate this row.")
open(os.path.join(HERE,"Table5_reliability.md"),"w").write("\n".join(L))
print("\nwrote reliability.json + Table5_reliability.md")
