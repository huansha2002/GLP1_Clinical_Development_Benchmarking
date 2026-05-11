"""02 - Enrollment Efficiency Analysis"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
 
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from src.config import SPONSORS
from src.utils import SPONSOR_COLORS, save_figure, sponsor_bar_chart
 
os.makedirs("figures", exist_ok=True)
df = pd.read_csv("data/processed/glp1_trials_processed.csv")
for c in ["start_date_parsed","primary_completion_date_parsed","completion_date_parsed","results_first_post_date_parsed"]:
    if c in df.columns: df[c] = pd.to_datetime(df[c], errors="coerce")
print(f"Loaded {len(df)} trials")
df = df[df["sponsor_normalized"].isin(["Eli Lilly", "Novo Nordisk"])]
 
df_enr = df[(df["study_type"]=="INTERVENTIONAL") & (df["enrollment_count"].notna()) & (df["enrollment_count"]>0)].copy()
phase_keep = ["Phase 1","Phase 2","Phase 3","Phase 4"]
df_enr = df_enr[df_enr["phase_simple"].isin(phase_keep)]
 
# 2.1 Enrollment Scale by Phase
fig, ax = plt.subplots(figsize=(10,6))
sns.boxplot(data=df_enr, x="phase_simple", y="enrollment_count", hue="sponsor_normalized",
            order=phase_keep, palette=SPONSOR_COLORS, showfliers=False, ax=ax)
ax.set_yscale("log"); ax.set_ylabel("Enrollment Count (log scale)"); ax.set_xlabel("Phase")
ax.set_title("Enrollment Scale by Phase - Lilly vs. Novo Nordisk", fontweight="bold")
ax.legend(title="Sponsor"); ax.spines[["top","right"]].set_visible(False)
fig.tight_layout(); save_figure(fig, "enrollment_scale_by_phase")
 
# 2.2 Enrollment Table
enr_table = df_enr.groupby(["sponsor_normalized","phase_simple"])["enrollment_count"].agg(["median","mean","count"]).round(0).unstack(level=0)
print("\nEnrollment by Phase:"); print(enr_table.to_string())
enr_table.to_csv("data/processed/enrollment_by_phase.csv")
 
# 2.3 Trial Duration
df_dur = df_enr[df_enr["duration_months"].notna() & (df_enr["duration_months"]>0) & (df_enr["duration_months"]<180)].copy()
fig, axes = plt.subplots(1,2,figsize=(14,5),sharey=True)
for i, phase in enumerate(["Phase 2","Phase 3"]):
    ax = axes[i]; sub = df_dur[df_dur["phase_simple"]==phase]
    for sp in ["Eli Lilly","Novo Nordisk"]:
        d = sub[sub["sponsor_normalized"]==sp]["duration_months"].dropna()
        if len(d)>0: ax.hist(d, bins=15, alpha=0.6, label=SPONSORS[sp]["short"], color=SPONSOR_COLORS[sp], edgecolor="white")
    ax.set_xlabel("Duration (months)"); ax.set_title(f"{phase} Trial Duration", fontweight="bold")
    ax.legend(); ax.spines[["top","right"]].set_visible(False)
axes[0].set_ylabel("Number of Trials")
fig.suptitle("Trial Duration Distribution", fontweight="bold", y=1.02)
fig.tight_layout(); save_figure(fig, "trial_duration_distribution")
 
# 2.4 Geographic Diversity
df_geo = df_enr[df_enr["n_countries"]>0].copy()
geo_data = {}
for phase in ["Phase 2","Phase 3"]:
    geo_data[phase] = {}
    for sp in ["Eli Lilly","Novo Nordisk"]:
        sub = df_geo[(df_geo["phase_simple"]==phase)&(df_geo["sponsor_normalized"]==sp)]
        geo_data[phase][sp] = sub["n_countries"].median() if len(sub)>0 else 0
sponsor_bar_chart(geo_data, "Median Countries per Trial", "Countries", "geographic_diversity")
 
# 2.5 Site Count
df_sites = df_enr[df_enr["n_sites"]>0].copy()
fig, ax = plt.subplots(figsize=(10,6))
sns.boxplot(data=df_sites, x="phase_simple", y="n_sites", hue="sponsor_normalized",
            order=phase_keep, palette=SPONSOR_COLORS, showfliers=False, ax=ax)
ax.set_ylabel("Number of Sites"); ax.set_xlabel("Phase")
ax.set_title("Trial Sites by Phase", fontweight="bold")
ax.legend(title="Sponsor"); ax.spines[["top","right"]].set_visible(False)
fig.tight_layout(); save_figure(fig, "site_count_by_phase")
 
# 2.6 Enrollment Efficiency
df_eff = df_enr[(df_enr["n_sites"]>0)&(df_enr["duration_months"]>0)].copy()
df_eff["eff"] = df_eff["enrollment_count"]/df_eff["n_sites"]/df_eff["duration_months"]
eff = df_eff.groupby(["sponsor_normalized","phase_simple"])["eff"].median().unstack(level=0).round(2)
print("\nEnrollment Efficiency (pts/site/month):"); print(eff.to_string())
eff.to_csv("data/processed/enrollment_efficiency.csv")
 
print("\nDone. Run 03_trial_design_analysis.py next.")
