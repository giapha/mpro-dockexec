#!/usr/bin/env python3
"""Render manuscript figures from released data. Run with dock env python (matplotlib)."""
import csv, json, os
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib.colors import ListedColormap
import numpy as np

HERE=os.path.dirname(os.path.abspath(__file__)); PKG=os.path.join(HERE,"..")
FIG=os.path.join(PKG,"figures"); os.makedirs(FIG,exist_ok=True)
FIELDS=["pdb_receptor","protein_chain","ligand_identifier","docking_software","software_version","grid_center","grid_size","search_effort","random_seed","receptor_preparation","ligand_preparation","protonation_tautomer","water_ion_handling","validation_redocking","code_artifacts","numeric_result"]
LBL={f:f.replace("_"," ") for f in FIELDS}
papers=list(csv.DictReader(open(os.path.join(PKG,"data","method_audit_candidate.csv"),encoding="utf-8")))
stats=json.load(open(os.path.join(HERE,"stats_v2.json")))
N=len(papers)
plt.rcParams.update({"font.size":9,"axes.spines.top":False,"axes.spines.right":False,"savefig.dpi":200,"savefig.bbox":"tight"})
GREEN,YEL,RED="#2c7fb8","#fdae61","#d7191c"

# ---- Figure 2: reporting completeness stacked, ranked ----
counts={f:{"reported":0,"partial":0,"missing":0} for f in FIELDS}
for p in papers:
    for f in FIELDS: counts[f][p[f]]=counts[f].get(p[f],0)+1
order=sorted(FIELDS,key=lambda f:counts[f]["reported"])
fig,ax=plt.subplots(figsize=(7.2,5.2))
y=np.arange(len(order))
rep=[counts[f]["reported"] for f in order]; par=[counts[f]["partial"] for f in order]; mis=[counts[f]["missing"] for f in order]
ax.barh(y,rep,color=GREEN,label="reported"); ax.barh(y,par,left=rep,color=YEL,label="partial")
ax.barh(y,mis,left=[rep[i]+par[i] for i in range(len(order))],color=RED,label="missing")
ax.set_yticks(y); ax.set_yticklabels([LBL[f] for f in order]); ax.set_xlabel(f"papers (N={N})")
ax.set_title("Reporting completeness across 16 docking fields"); ax.legend(loc="lower right",frameon=False)
for i,f in enumerate(order): ax.text(N+0.2,i,f"{100*rep[i]/N:.0f}%",va="center",fontsize=8)
ax.set_xlim(0,N+3); fig.savefig(os.path.join(FIG,"Figure2_reporting_completeness.png")); plt.close(fig)

# ---- Figure 3: missing-parameter matrix ----
state2v={"reported":0,"partial":1,"missing":2}
M=np.array([[state2v.get(p[f],2) for f in order] for p in sorted(papers,key=lambda x:x["paper_id"])])
fig,ax=plt.subplots(figsize=(7.6,7.2))
cmap=ListedColormap([GREEN,YEL,RED])
ax.imshow(M,aspect="auto",cmap=cmap,vmin=0,vmax=2)
ax.set_xticks(range(len(order))); ax.set_xticklabels([LBL[f] for f in order],rotation=90,fontsize=7)
ax.set_yticks(range(len(papers))); ax.set_yticklabels([p["paper_id"] for p in sorted(papers,key=lambda x:x["paper_id"])],fontsize=6)
ax.set_title("Missing-parameter matrix (paper × field)")
from matplotlib.patches import Patch
ax.legend(handles=[Patch(color=GREEN,label="reported"),Patch(color=YEL,label="partial"),Patch(color=RED,label="missing")],
          loc="upper left",bbox_to_anchor=(1.01,1),frameon=False,fontsize=8)
fig.savefig(os.path.join(FIG,"Figure3_missing_parameter_matrix.png")); plt.close(fig)

# ---- Figure 4: claim-level E0-E4 with Wilson CI ----
ce=stats["primary"]["claim_level_E_PRIMARY"]; nC=stats["primary"]["N_claims"]
ks=["E1","E2","E3"]; pct=[ce[k]["pct"] for k in ks]; lo=[ce[k]["pct"]-ce[k]["ci_naive"][0] for k in ks]; hi=[ce[k]["ci_naive"][1]-ce[k]["pct"] for k in ks]
fig,ax=plt.subplots(figsize=(5.0,4.2))
bars=ax.bar(ks,pct,color=["#d7191c","#fdae61","#2c7fb8"],yerr=[lo,hi],capsize=5,edgecolor="k",linewidth=0.5)
for k,b in zip(ks,bars): ax.text(b.get_x()+b.get_width()/2,b.get_height()+2,f"{ce[k]['pct']}%\n({ce[k]['n']})",ha="center",fontsize=8)
ax.set_ylabel(f"% of claims (N={nC})"); ax.set_ylim(0,75)
ax.set_title("Claim-level executability E0–E4 (Wilson 95% CI)")
ax.text(0.5,-0.18,"E0=0, E4=0 (none observed)",transform=ax.transAxes,ha="center",fontsize=8,style="italic")
fig.savefig(os.path.join(FIG,"Figure4_executability_distribution.png")); plt.close(fig)

# ---- Figure 1: pipeline schematic ----
fig,ax=plt.subplots(figsize=(11,2.4)); ax.axis("off"); ax.set_xlim(0,7); ax.set_ylim(0,1)
steps=["Retrieve\nOA full text","LLM candidate\nextraction\n(+ source spans)","Deterministic\nspan verification\n(anti-fabrication)","Adversarial\nE-class\nadjudication","Human\ncountersignature\n[pending κ]","Re-execution\n(AutoDock Vina)","Evidence\nrecord"]
cols=["#deebf7","#deebf7","#c7e9b4","#deebf7","#fee0b6","#c7e9b4","#e5d8f0"]
w=0.92
for i,(s,c) in enumerate(zip(steps,cols)):
    x=i*1.0+0.04
    ax.add_patch(FancyBboxPatch((x,0.25),w,0.5,boxstyle="round,pad=0.02",fc=c,ec="k",lw=0.8))
    ax.text(x+w/2,0.5,s,ha="center",va="center",fontsize=7.5)
    if i<len(steps)-1: ax.add_patch(FancyArrowPatch((x+w,0.5),(x+1.0,0.5),arrowstyle="-|>",mutation_scale=10,lw=1,color="k"))
ax.set_title("Figure 1. Source-verified, agent-assisted audit + re-execution pipeline",fontsize=9,loc="left")
fig.savefig(os.path.join(FIG,"Figure1_pipeline.png")); plt.close(fig)

# ---- Figure 6: MERS-Dock tiers -> E-ladder ----
fig,ax=plt.subplots(figsize=(8.5,4.6)); ax.axis("off"); ax.set_xlim(0,10); ax.set_ylim(0,10)
tiers=[("Tier 1 — execution-blocking","receptor ID · box centre · box size · software · ligand ID","#fdd0a2",7.2),
       ("Tier 2 — assumption-forcing","version · scoring · search effort · prep · protonation · water/ion · chain","#fee391",4.4),
       ("Tier 3 — robustness","random seed · validation/redocking · reusable artifacts","#c7e9b4",1.6)]
for t,items,c,yy in tiers:
    ax.add_patch(FancyBboxPatch((0.2,yy),5.3,2.0,boxstyle="round,pad=0.05",fc=c,ec="k",lw=0.8))
    ax.text(2.85,yy+1.45,t,ha="center",fontsize=8.5,weight="bold"); ax.text(2.85,yy+0.6,items,ha="center",fontsize=6.8,wrap=True)
ladder=[("E1 blocked (Tier-1 missing)",8.0),("E2 assumptions (Tier-2 gaps)",6.0),("E3 executable (Tier-1+2)",4.0),("E4 robust (Tier-3 + seed)",2.0)]
for t,yy in ladder:
    ax.add_patch(FancyBboxPatch((6.6,yy),3.2,1.4,boxstyle="round,pad=0.04",fc="#deebf7",ec="k",lw=0.8))
    ax.text(8.2,yy+0.7,t,ha="center",fontsize=7.5)
ax.annotate("",xy=(6.6,8.7),xytext=(5.5,8.2),arrowprops=dict(arrowstyle="-|>"))
ax.annotate("",xy=(6.6,6.7),xytext=(5.5,5.4),arrowprops=dict(arrowstyle="-|>"))
ax.annotate("",xy=(6.6,4.7),xytext=(5.5,2.6),arrowprops=dict(arrowstyle="-|>"))
ax.set_title("Figure 6. MERS-Dock reporting tiers map to the executability ladder",fontsize=9,loc="left")
fig.savefig(os.path.join(FIG,"Figure6_MERSdock_ladder.png")); plt.close(fig)

print("rendered:", sorted(os.listdir(FIG)))
