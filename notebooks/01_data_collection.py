"""01 - Data Collection from ClinicalTrials.gov API"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
 
import pandas as pd
from src.ct_api import fetch_glp1_trials
from src.utils import add_parsed_dates, get_phase_simple, calc_duration_months
 
print("=" * 60)
print("Fetching GLP-1 trials from ClinicalTrials.gov v2 API ...")
print("=" * 60)
 
df_raw = fetch_glp1_trials()
print(f"\nTotal trials (after sponsor filter): {len(df_raw)}")
print(f"  Eli Lilly:    {(df_raw['sponsor_normalized'] == 'Eli Lilly').sum()}")
print(f"  Novo Nordisk: {(df_raw['sponsor_normalized'] == 'Novo Nordisk').sum()}")
 
os.makedirs("data/raw", exist_ok=True)
df_raw.to_csv("data/raw/glp1_trials_raw.csv", index=False)
print("Saved -> data/raw/glp1_trials_raw.csv")
 
df = df_raw.copy()
df = add_parsed_dates(df)
df["phase_simple"] = df["phases"].apply(get_phase_simple)
df["start_year"] = df["start_date_parsed"].dt.year
df["completion_year"] = df["primary_completion_date_parsed"].dt.year
df["duration_months"] = calc_duration_months(
    df["start_date_parsed"], df["primary_completion_date_parsed"])
df["n_countries"] = df["location_countries"].apply(
    lambda x: len(str(x).split("|")) if pd.notna(x) and x != "" else 0)
 
os.makedirs("data/processed", exist_ok=True)
df.to_csv("data/processed/glp1_trials_processed.csv", index=False)
print("Saved -> data/processed/glp1_trials_processed.csv")
 
print("\n" + "=" * 60)
for sp in ["Eli Lilly", "Novo Nordisk"]:
    sub = df[df["sponsor_normalized"] == sp]
    print(f"\n--- {sp} ---")
    print(f"  Total: {len(sub)}  |  Median enrollment: {sub['enrollment_count'].median():.0f}")
    for ph, cnt in sub["phase_simple"].value_counts().items():
        print(f"    {ph:20s} {cnt}")
 
print("\nDone. Run 02_enrollment_analysis.py next.")
