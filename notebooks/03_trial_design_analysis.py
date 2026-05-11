"""03 - Trial Design Pattern Analysis"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
 
import pandas as pd, numpy as np, matplotlib.pyplot as plt, seaborn as sns
from src.config import SPONSORS
from src.utils import SPONSOR_COLORS, save_figure
 
os.makedirs("figures", exist_ok=True)
df = pd.read_csv("data/processed/glp1_trials_processed.csv")
for c in ["start_date_parsed","primary_completion_date_parsed"]:
    if c in df.columns: df[c] = pd.to_datetime(df[c], errors="coerce")
df = df[df["study_type"]=="INTERVENTIONAL"].copy()
print(f"Interventional trials: {len(df)}")
df = df[df["sponsor_normalized"].isin(["Eli Lilly", "Novo Nordisk"])]
 
# 3.1 Phase Distribution
phase_keep = ["Phase 1","Phase 1/2","Phase 2","Phase 2/3","Phase 3","Phase 4"]
df_ph = df[df["phase_simple"].isin(phase_keep)]
ct = pd.crosstab(df_ph["phase_simple"], df_ph["sponsor_normalized"]).reindex(phase_keep).fillna(0).astype(int)
ct_pct = ct.div(ct.sum(axis=0), axis=1)*100
fig, axes = plt.subplots(1,2,figsize=(14,5))
ct.plot(kind="bar", ax=axes[0], color=[SPONSOR_COLORS[c] for c in ct.columns], edgecolor="white")
axes[0].set_title("Trial Count by Phase", fontweight="bold"); axes[0].set_ylabel("Trials"); axes[0].set_xlabel("")
axes[0].legend(title=""); axes[0].spines[["top","right"]].set_visible(False)
ct_pct.plot(kind="bar", ax=axes[1], color=[SPONSOR_COLORS[c] for c in ct_pct.columns], edgecolor="white")
axes[1].set_title("Phase Distribution (%)", fontweight="bold"); axes[1].set_ylabel("%"); axes[1].set_xlabel("")
axes[1].legend(title=""); axes[1].spines[["top","right"]].set_visible(False)
fig.suptitle("Portfolio Phase Balance", fontweight="bold", y=1.02)
fig.tight_layout(); save_figure(fig, "phase_distribution")
 
# 3.2 Indication
def classify_ind(c):
    if pd.isna(c): return "Other"
    c = c.lower()
    if any(k in c for k in ["obesity","overweight","weight loss","weight management"]): return "Obesity / Weight"
    elif any(k in c for k in ["nash","nafld","fatty liver"]): return "NASH / Liver"
    elif any(k in c for k in ["heart failure","cardiovascular","cardiac","stroke"]): return "Cardiovascular"
    elif any(k in c for k in ["kidney","renal","nephropathy"]): return "Renal"
    elif any(k in c for k in ["alzheimer","parkinson"]): return "Neurodegeneration"
    elif any(k in c for k in ["diabetes","t2dm","type 2","glycemic","hba1c"]): return "Type 2 Diabetes"
    elif any(k in c for k in ["sleep apnea"]): return "Sleep Apnea"
    else: return "Other"
df["indication"] = df["conditions"].apply(classify_ind)
ind_ct = pd.crosstab(df["indication"], df["sponsor_normalized"]).sort_values(df["sponsor_normalized"].unique()[0], ascending=True)
fig, ax = plt.subplots(figsize=(10,6))
ind_ct.plot(kind="barh", ax=ax, color=[SPONSOR_COLORS[c] for c in ind_ct.columns], edgecolor="white")
ax.set_xlabel("Trials"); ax.set_title("Indication Breadth - GLP-1 Programs", fontweight="bold")
ax.legend(title=""); ax.spines[["top","right"]].set_visible(False)
fig.tight_layout(); save_figure(fig, "indication_mapping")
 
# 3.3 Endpoints
def classify_ep(e):
    if pd.isna(e): return "Not specified"
    e = e.lower()
    if any(k in e for k in ["hba1c","a1c"]): return "HbA1c"
    elif any(k in e for k in ["body weight","weight change","weight loss","bmi"]): return "Body Weight"
    elif any(k in e for k in ["mace","cardiovascular death"]): return "CV Events (MACE)"
    elif any(k in e for k in ["safety","adverse event","tolerability"]): return "Safety / Tolerability"
    elif any(k in e for k in ["pharmacokinetic","auc","cmax","bioavailability"]): return "PK / Bioavailability"
    elif any(k in e for k in ["egfr","kidney","renal"]): return "Renal"
    elif any(k in e for k in ["liver","fibrosis","nash"]): return "Liver / NASH"
    else: return "Other"
df["endpoint_cat"] = df["primary_outcome_measures"].apply(classify_ep)
ep_ct = pd.crosstab(df["endpoint_cat"], df["sponsor_normalized"])
fig, ax = plt.subplots(figsize=(10,6))
ep_ct.plot(kind="barh", ax=ax, color=[SPONSOR_COLORS[c] for c in ep_ct.columns], edgecolor="white")
ax.set_xlabel("Trials"); ax.set_title("Primary Endpoint Category", fontweight="bold")
ax.legend(title=""); ax.spines[["top","right"]].set_visible(False)
fig.tight_layout(); save_figure(fig, "endpoint_classification")
 
# 3.4 Masking
mask_ct = pd.crosstab(df["masking"], df["sponsor_normalized"])
mask_pct = mask_ct.div(mask_ct.sum(axis=0), axis=1)*100
fig, ax = plt.subplots(figsize=(10,5))
mask_pct.plot(kind="barh", ax=ax, color=[SPONSOR_COLORS[c] for c in mask_pct.columns], edgecolor="white")
ax.set_xlabel("% of Trials"); ax.set_title("Masking Strategy", fontweight="bold")
ax.legend(title=""); ax.spines[["top","right"]].set_visible(False)
fig.tight_layout(); save_figure(fig, "masking_strategy")
 
# 3.5 Design Summary
rows = []
for sp in ["Eli Lilly","Novo Nordisk"]:
    s = df[df["sponsor_normalized"]==sp]
    rows.append({"Sponsor": SPONSORS[sp]["short"], "Trials": len(s),
        "Indications": s["indication"].nunique(),
        "Top Indication": s["indication"].mode().iloc[0] if len(s)>0 else "",
        "Top Endpoint": s["endpoint_cat"].mode().iloc[0] if len(s)>0 else "",
        "% Double-Blind": f"{s['masking'].str.contains('DOUBLE',case=False,na=False).sum()/len(s)*100:.1f}%",
        "% Randomized": f"{s['allocation'].str.contains('RANDOM',case=False,na=False).sum()/len(s)*100:.1f}%"})
dd = pd.DataFrame(rows); print("\nDesign Summary:"); print(dd.to_string(index=False))
dd.to_csv("data/processed/trial_design_summary.csv", index=False)
 
# 3.6 Temporal Trend
df["start_year"] = pd.to_datetime(df["start_date_parsed"], errors="coerce").dt.year
dy = df[(df["start_year"]>=2010)&(df["start_year"]<=2025)]
yc = pd.crosstab(dy["start_year"], dy["sponsor_normalized"])
fig, ax = plt.subplots(figsize=(12,5))
for sp in ["Eli Lilly","Novo Nordisk"]:
    if sp in yc.columns: ax.plot(yc.index, yc[sp], marker="o", color=SPONSOR_COLORS[sp], label=SPONSORS[sp]["short"], linewidth=2)
ax.set_xlabel("Year"); ax.set_ylabel("New Trials"); ax.set_title("GLP-1 Program Activity Over Time", fontweight="bold")
ax.legend(); ax.spines[["top","right"]].set_visible(False)
fig.tight_layout(); save_figure(fig, "trials_per_year_trend")
 
print("\nDone. Run 04_success_proxy_analysis.py next.")
