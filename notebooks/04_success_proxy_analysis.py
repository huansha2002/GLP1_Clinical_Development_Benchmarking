"""04 - Development Success Proxies"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
 
import pandas as pd, numpy as np, matplotlib.pyplot as plt, seaborn as sns
from matplotlib.patches import Patch
from src.config import SPONSORS, GLP1_DRUGS
from src.utils import SPONSOR_COLORS, save_figure, sponsor_bar_chart
 
os.makedirs("figures", exist_ok=True)
df = pd.read_csv("data/processed/glp1_trials_processed.csv")
for c in ["start_date_parsed","primary_completion_date_parsed","completion_date_parsed","results_first_post_date_parsed"]:
    if c in df.columns: df[c] = pd.to_datetime(df[c], errors="coerce")
df = df[df["study_type"]=="INTERVENTIONAL"].copy()
print(f"Interventional trials: {len(df)}")
df = df[df["sponsor_normalized"].isin(["Eli Lilly", "Novo Nordisk"])]
 
# 4.1 Status Distribution
sg = {"Completed":["COMPLETED"],"Active/Recruiting":["RECRUITING","ACTIVE_NOT_RECRUITING","ENROLLING_BY_INVITATION","NOT_YET_RECRUITING"],
      "Terminated":["TERMINATED"],"Withdrawn":["WITHDRAWN"],"Suspended":["SUSPENDED"]}
def msg(s):
    for g, ss in sg.items():
        if s in ss: return g
    return "Other"
df["status_group"] = df["overall_status"].apply(msg)
sc = pd.crosstab(df["status_group"], df["sponsor_normalized"])
sp = sc.div(sc.sum(axis=0), axis=1)*100
fig, axes = plt.subplots(1,2,figsize=(14,5))
sc.plot(kind="barh", ax=axes[0], color=[SPONSOR_COLORS[c] for c in sc.columns], edgecolor="white")
axes[0].set_xlabel("Trials"); axes[0].set_title("Status - Counts", fontweight="bold")
axes[0].legend(title=""); axes[0].spines[["top","right"]].set_visible(False)
sp.plot(kind="barh", ax=axes[1], color=[SPONSOR_COLORS[c] for c in sp.columns], edgecolor="white")
axes[1].set_xlabel("%"); axes[1].set_title("Status - %", fontweight="bold")
axes[1].legend(title=""); axes[1].spines[["top","right"]].set_visible(False)
fig.suptitle("Trial Outcome Distribution", fontweight="bold", y=1.02)
fig.tight_layout(); save_figure(fig, "trial_status_distribution")
 
# 4.2 Attrition
pk = ["Phase 1","Phase 2","Phase 3"]
dc = df[df["status_group"].isin(["Completed","Terminated","Withdrawn"]) & df["phase_simple"].isin(pk)]
ad = {}
for p in pk:
    ad[p] = {}
    for s in ["Eli Lilly","Novo Nordisk"]:
        sub = dc[(dc["phase_simple"]==p)&(dc["sponsor_normalized"]==s)]
        t = len(sub); f = sub["status_group"].isin(["Terminated","Withdrawn"]).sum()
        ad[p][s] = round(f/t*100,1) if t>0 else 0
sponsor_bar_chart(ad, "Trial Attrition Rate by Phase", "Attrition Rate (%)", "attrition_rate_by_phase")
print("\nAttrition:")
for p, r in ad.items(): print(f"  {p}: Lilly={r.get('Eli Lilly',0):.1f}%, Novo={r.get('Novo Nordisk',0):.1f}%")
 
# 4.3 Termination Reasons
dt = df[df["overall_status"]=="TERMINATED"]
if len(dt)>0 and dt["why_stopped"].notna().any():
    print("\nTermination Reasons:")
    for s in ["Eli Lilly","Novo Nordisk"]:
        sub = dt[dt["sponsor_normalized"]==s]
        print(f"  {SPONSORS[s]['short']} ({len(sub)}):")
        for r in sub["why_stopped"].dropna(): print(f"    - {r[:120]}")
 
# 4.4 Development Timeline
dtl = df[df["glp1_drugs_matched"].notna() & (df["glp1_drugs_matched"]!="")].copy()
dtl["drug_list"] = dtl["glp1_drugs_matched"].str.split("|")
dtl = dtl.explode("drug_list")
recs = []
for drug in dtl["drug_list"].unique():
    sub = dtl[dtl["drug_list"]==drug]
    sponsor = sub["sponsor_normalized"].mode().iloc[0] if len(sub)>0 else "?"
    p1s = sub.loc[sub["phase_simple"].isin(["Phase 1","Phase 1/2"]),"start_date_parsed"].min()
    p3e = sub.loc[sub["phase_simple"].isin(["Phase 3","Phase 2/3"]),"primary_completion_date_parsed"].max()
    span = round((p3e-p1s).days/365.25,1) if pd.notna(p1s) and pd.notna(p3e) else None
    recs.append({"drug":drug,"sponsor":sponsor,"n_trials":len(sub),"dev_span_years":span})
tl = pd.DataFrame(recs).sort_values("dev_span_years")
print("\nDev Timeline:"); print(tl[["drug","sponsor","n_trials","dev_span_years"]].to_string(index=False))
tl.to_csv("data/processed/development_timeline.csv", index=False)
 
tlp = tl[tl["dev_span_years"].notna()]
if len(tlp)>0:
    fig, ax = plt.subplots(figsize=(10,max(4,len(tlp)*0.6)))
    colors = [SPONSOR_COLORS.get(s,"gray") for s in tlp["sponsor"]]
    ax.barh(tlp["drug"], tlp["dev_span_years"], color=colors, edgecolor="white", height=0.6)
    ax.set_xlabel("Years: Phase 1 Start -> Phase 3 Completion")
    ax.set_title("Development Timeline by Drug", fontweight="bold")
    ax.legend(handles=[Patch(facecolor=SPONSOR_COLORS[s], label=SPONSORS[s]["short"]) for s in SPONSORS])
    ax.spines[["top","right"]].set_visible(False); fig.tight_layout(); save_figure(fig, "development_timeline_by_drug")
 
# 4.5 Reporting Lag
dr = df[df["primary_completion_date_parsed"].notna() & df["results_first_post_date_parsed"].notna()].copy()
dr["lag"] = (dr["results_first_post_date_parsed"]-dr["primary_completion_date_parsed"]).dt.days
dr = dr[dr["lag"]>0]
if len(dr)>5:
    fig, ax = plt.subplots(figsize=(10,5))
    for s in ["Eli Lilly","Novo Nordisk"]:
        d = dr[dr["sponsor_normalized"]==s]["lag"]
        if len(d)>0: ax.hist(d, bins=20, alpha=0.6, label=SPONSORS[s]["short"], color=SPONSOR_COLORS[s], edgecolor="white")
    ax.axvline(x=365, color="red", linestyle="--", linewidth=1.5, label="FDAAA 801 (365d)")
    ax.set_xlabel("Days"); ax.set_ylabel("Trials"); ax.set_title("Results Reporting Lag", fontweight="bold")
    ax.legend(); ax.spines[["top","right"]].set_visible(False); fig.tight_layout(); save_figure(fig, "results_reporting_lag")
    print("\nReporting Lag:")
    for s in ["Eli Lilly","Novo Nordisk"]:
        d = dr[dr["sponsor_normalized"]==s]["lag"]
        if len(d)>0: print(f"  {SPONSORS[s]['short']}: median={d.median():.0f}d, n={len(d)}")
 
print("\nDone. Run 05_benchmarking_dashboard.py next.")
