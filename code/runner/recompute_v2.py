#!/usr/bin/env python3
"""Recompute re-execution stats for the corrected-box / expanded-n run (v2):
reported box sizes + P0001/P0053 added (n_E3 5->10). QC = drop rerun > -2.
Outputs medians, within-tolerance, Mann-Whitney P, bootstrap CIs; compares to v1."""
import csv, statistics as st, random, json, os, math
random.seed(2026)
HERE=os.path.dirname(os.path.abspath(__file__))
DATA=os.path.join(os.path.dirname(os.path.dirname(HERE)),"data","reexecution")  # repo data/reexecution
def load(p):
    if not os.path.exists(p): return []
    return [x for x in csv.DictReader(open(p)) if x.get('rerun_score','').strip() and x.get('abs_delta','').strip()]
def stats(rows):
    qc=[x for x in rows if float(x['rerun_score'])<=-2.0]
    g=lambda e:[abs(float(x['abs_delta'])) for x in qc if x['e_class']==e]
    e3,e2=g('E3'),g('E2'); allD=[abs(float(x['abs_delta'])) for x in qc]
    def med(x): return round(st.median(x),3) if x else None
    def wtol(x): return f"{sum(1 for d in x if d<=2)}/{len(x)}" if x else "0/0"
    def boot(x,n=5000):
        if len(x)<2: return [None,None]
        m=sorted(st.median([random.choice(x) for _ in x]) for _ in range(n)); return [round(m[int(.025*n)],2),round(m[int(.975*n)],2)]
    def mwu(a,b):
        if len(a)<2 or len(b)<2: return None
        comb=sorted([(v,0) for v in a]+[(v,1) for v in b]); rank=[0]*len(comb); i=0
        while i<len(comb):
            j=i
            while j<len(comb) and comb[j][0]==comb[i][0]: j+=1
            for k in range(i,j): rank[k]=(i+1+j)/2
            i=j
        n1,n2=len(a),len(b); R1=sum(rank[k] for k in range(len(comb)) if comb[k][1]==0)
        U1=R1-n1*(n1+1)/2; U=min(U1,n1*n2-U1); mu=n1*n2/2; sd=(n1*n2*(n1+n2+1)/12)**.5
        z=(U-mu)/sd; return round(2*min(0.5*(1+math.erf(z/2**.5)),0.5*(1-math.erf(z/2**.5))),4)
    return {"n_qc":len(qc),"E3_n":len(e3),"E2_n":len(e2),
            "ALL_median":med(allD),"ALL_within2":wtol(allD),
            "E3_median":med(e3),"E3_CI":boot(e3),"E3_within2":wtol(e3),
            "E2_median":med(e2),"E2_CI":boot(e2),"E2_within2":wtol(e2),
            "mannwhitney_p":mwu(e3,e2)}
v2=stats(load(os.path.join(DATA,"reproduction_outcomes.csv")))
v1=stats(load(os.path.join(DATA,"reproduction_outcomes_v1_default25.csv")))
res={"v2_reported_box_expanded_n":v2,"v1_default25":v1}
json.dump(res,open(os.path.join(DATA,"reproduction_v2_stats.json"),"w"),indent=2)
print("=== V2 (reported boxes + n_E3 expanded) ===")
print(json.dumps(v2,indent=1))
print("\n=== V1 (default 25A, for comparison) ===")
print(json.dumps(v1,indent=1))
sig="SIGNIFICANT" if (v2.get("mannwhitney_p") or 1)<0.05 else "not significant"
print(f"\n>>> V2 E3-vs-E2 Mann-Whitney P={v2.get('mannwhitney_p')} -> {sig} (n_E3={v2['E3_n']})")
