"""Shared analysis utilities."""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from src.config import SPONSORS, PHASE_ORDER, PHASE_LABELS
 
sns.set_theme(style="whitegrid", font_scale=1.1)
SPONSOR_COLORS = {sp: info["color"] for sp, info in SPONSORS.items()}
 
 
def parse_ct_date(date_str):
    if not date_str or pd.isna(date_str):
        return pd.NaT
    try:
        return pd.to_datetime(date_str)
    except Exception:
        try:
            return pd.to_datetime(date_str, format="%Y-%m")
        except Exception:
            try:
                return pd.to_datetime(date_str, format="%B %Y")
            except Exception:
                return pd.NaT 
 
def add_parsed_dates(df):
    for col in ["start_date", "primary_completion_date",
                "completion_date", "results_first_post_date"]:
        if col in df.columns:
            df[col + "_parsed"] = df[col].apply(parse_ct_date)
    return df
 
 
def get_phase_simple(phase_str):
    if not phase_str or pd.isna(phase_str):
        return "N/A"
    ps = str(phase_str).upper()
    for po in PHASE_ORDER:
        if po in ps:
            return PHASE_LABELS.get(po, ps)
    return "N/A"
 
 
def calc_duration_months(start, end):
    return (end - start).dt.days / 30.44
 
 
def save_figure(fig, name, dpi=150):
    path = f"figures/{name}.png"
    fig.savefig(path, dpi=dpi, bbox_inches="tight", facecolor="white")
    print(f"  Saved: {path}")
    plt.close(fig)
 
 
def sponsor_bar_chart(data, title, ylabel, filename, fmt=".1f", figsize=(8, 5)):
    categories = list(data.keys())
    sponsors_list = list(SPONSORS.keys())
    x = np.arange(len(categories))
    width = 0.35
    fig, ax = plt.subplots(figsize=figsize)
    for i, sp in enumerate(sponsors_list):
        vals = [data[cat].get(sp, 0) for cat in categories]
        bars = ax.bar(x + i * width, vals, width, label=SPONSORS[sp]["short"],
                      color=SPONSOR_COLORS[sp], edgecolor="white")
        for bar, val in zip(bars, vals):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                    f"{val:{fmt}}", ha="center", va="bottom", fontsize=9)
    ax.set_ylabel(ylabel)
    ax.set_title(title, fontweight="bold")
    ax.set_xticks(x + width / 2)
    ax.set_xticklabels(categories, rotation=30, ha="right")
    ax.legend()
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    save_figure(fig, filename)
