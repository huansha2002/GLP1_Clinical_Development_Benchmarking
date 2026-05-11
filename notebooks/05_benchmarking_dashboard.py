"""05 - Integrated Benchmarking Dashboard"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
 
import pandas as pd, numpy as np, matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from src.config import SPONSORS
from src.utils import SPONSOR_COLORS, save_figure
 
os.makedirs("figures", exist_ok=True)
df = pd.read_csv("data/processed/glp1_trials_processed.csv")
for c in ["start_date_parsed","primary_completion_date_parsed","completion_date_parsed","results_first_post_date_parsed"]:
    if c in df.columns: df[c] = pd.to_datetime(df[c], errors="coerce")
df = df[df["study_type"]=="INTERVENTIONAL"].copy()
 
def scorecard(df, sponsor):
    s = df[df["sponsor_normalized"]==sponsor].copy()
    n = len(s); nd = s["glp1_drugs_matched"].nunique()
    def ci(c):
        if pd.isna(c): return "Other"
        c=c.lower()
        if any(k in c for k in ["obesity","overweight","weight"]): return "Obesity"
        elif any(k in c for k in ["diabetes","t2dm","type 2","hba1c"]): return "T2DM"
        elif any(k in c for k in ["cardiovascular","heart","mace"]): return "CV"
        elif any(k in c for k in ["nash","liver"]): return "NASH"
        elif any(k in c for k in ["kidney","renal"]): return "Renal"
        elif any(k in c for k in ["alzheimer","parkinson"]): return "Neuro"
        elif any(k in c for k in ["sleep apnea"]): return "Sleep Apnea"
        else: return "Other"
    s["_i"] = s["conditions"].apply(ci); ni = s["_i"].nunique()
    se = s[(s["enrollment_count"].notna())&(s["enrollment_count"]>0)]
    me = se["enrollment_count"].median() if len(se)>0 else 0
    sef = se[(se["n_sites"]>0)&(se["duration_months"].notna())&(se["duration_months"]>0)].copy()
    if len(sef)>0: sef["e"]=sef["enrollment_count"]/sef["n_sites"]/sef["duration_months"]; ee=sef["e"].median()
    else: ee=0
    sg = s[s["n_countries"]>0]; mc=sg["n_countries"].median() if len(sg)>0 else 0; ms=sg["n_sites"].median() if len(sg)>0 else 0
    pr = s["allocation"].str.contains("RANDOM",case=False,na=False).sum()/max(n,1)*100
    pd2 = s["masking"].str.contains("DOUBLE",case=False,na=False).sum()/max(n,1)*100
    con = s[s["overall_status"].isin(["COMPLETED","TERMINATED","WITHDRAWN"])]
    cr = (con["overall_status"]=="COMPLETED").sum()/max(len(con),1)*100
    p3 = con[con["phase_simple"]=="Phase 3"]; p3a=(1-(p3["overall_status"]=="COMPLETED").sum()/max(len(p3),1))*100
    sr = s[s["primary_completion_date_parsed"].notna()&s["results_first_post_date_parsed"].notna()].copy()
    if len(sr)>0:
        sr["l"]=(sr["results_first_post_date_parsed"]-sr["primary_completion_date_parsed"]).dt.days; sr=sr[sr["l"]>0]
        ml=sr["l"].median() if len(sr)>0 else np.nan; pw=(sr["l"]<=365).sum()/max(len(sr),1)*100 if len(sr)>0 else np.nan
    else: ml=np.nan; pw=np.nan
    return {"Sponsor":SPONSORS[sponsor]["short"],"Total GLP-1 Trials":n,"Unique Drugs":nd,"Indication Breadth":ni,
        "Median Enrollment":me,"Enrollment Efficiency (pts/site/mo)":round(ee,2),
        "Median Countries/Trial":mc,"Median Sites/Trial":ms,
        "% Randomized":round(pr,1),"% Double-Blind":round(pd2,1),
        "Trial Completion Rate (%)":round(cr,1),"Phase 3 Attrition (%)":round(p3a,1),
        "Median Reporting Lag (days)":round(ml,0) if pd.notna(ml) else "N/A",
        "% Results within 365 days":round(pw,1) if pd.notna(pw) else "N/A"}
 
sl = scorecard(df,"Eli Lilly"); sn = scorecard(df,"Novo Nordisk")
sdf = pd.DataFrame([sl,sn]).set_index("Sponsor").T
print("\n"+"="*60+"\n  CLINICAL DEVELOPMENT EFFICIENCY SCORECARD\n"+"="*60)
print(sdf.to_string()); sdf.to_csv("data/processed/benchmarking_scorecard.csv")
 
# Visual Scorecard
cats = {"Portfolio Scope":["Total GLP-1 Trials","Unique Drugs","Indication Breadth"],
    "Enrollment":["Median Enrollment","Enrollment Efficiency (pts/site/mo)"],
    "Geographic":["Median Countries/Trial","Median Sites/Trial"],
    "Design Quality":["% Randomized","% Double-Blind"],
    "Success":["Trial Completion Rate (%)","Phase 3 Attrition (%)"],
    "Transparency":["Median Reporting Lag (days)","% Results within 365 days"]}
fig = plt.figure(figsize=(16,10))
fig.suptitle("Cross-Company Clinical Development Efficiency Scorecard\nGLP-1 Programs - Lilly vs. Novo Nordisk", fontsize=14, fontweight="bold", y=0.98)
gs = gridspec.GridSpec(3,2,hspace=0.4,wspace=0.3)
for idx,(cn,inds) in enumerate(cats.items()):
    r,c=divmod(idx,2); ax=fig.add_subplot(gs[r,c]); ax.set_title(cn, fontweight="bold", fontsize=11); ax.axis("off")
    ct=[]
    for i in inds:
        if i in sdf.index: ct.append([i,str(sdf.loc[i,"Lilly"]),str(sdf.loc[i,"Novo"])])
    if ct:
        t=ax.table(cellText=ct,colLabels=["Indicator","Lilly","Novo"],cellLoc="center",loc="center")
        t.auto_set_font_size(False); t.set_fontsize(9); t.scale(1.0,1.4)
        for j in range(3): t[0,j].set_facecolor("#2c3e50"); t[0,j].set_text_props(color="white",fontweight="bold")
        for i in range(1,len(ct)+1):
            for j in range(3):
                if i%2==0: t[i,j].set_facecolor("#f8f9fa")
                if j==1: t[i,j].set_text_props(color=SPONSOR_COLORS["Eli Lilly"])
                elif j==2: t[i,j].set_text_props(color=SPONSOR_COLORS["Novo Nordisk"])
fig.tight_layout(rect=[0,0,1,0.94]); save_figure(fig, "benchmarking_scorecard_visual")
 
# Radar Chart
ri=["Total GLP-1 Trials","Indication Breadth","Enrollment Efficiency (pts/site/mo)","% Double-Blind","Trial Completion Rate (%)"]
sl2=["Trials","Indications","Enrollment\nEfficiency","% Double-\nBlind","Completion\nRate"]
lr,nr=[],[]
for i in ri:
    lv=pd.to_numeric(sdf.loc[i,"Lilly"],errors="coerce"); nv=pd.to_numeric(sdf.loc[i,"Novo"],errors="coerce")
    lr.append(lv if pd.notna(lv) else 0); nr.append(nv if pd.notna(nv) else 0)
mx=[max(l,n,1) for l,n in zip(lr,nr)]
ln2=[l/m for l,m in zip(lr,mx)]; nn2=[n/m for n,m in zip(nr,mx)]
ang=np.linspace(0,2*np.pi,len(ri),endpoint=False).tolist()
ln2+=ln2[:1]; nn2+=nn2[:1]; ang+=ang[:1]
fig,ax=plt.subplots(figsize=(8,8),subplot_kw=dict(polar=True))
ax.fill(ang,ln2,alpha=0.15,color=SPONSOR_COLORS["Eli Lilly"])
ax.plot(ang,ln2,"o-",linewidth=2,color=SPONSOR_COLORS["Eli Lilly"],label="Lilly")
ax.fill(ang,nn2,alpha=0.15,color=SPONSOR_COLORS["Novo Nordisk"])
ax.plot(ang,nn2,"s-",linewidth=2,color=SPONSOR_COLORS["Novo Nordisk"],label="Novo")
ax.set_xticks(ang[:-1]); ax.set_xticklabels(sl2,fontsize=10); ax.set_ylim(0,1.1)
ax.set_title("Normalized Efficiency Comparison", fontweight="bold", pad=20)
ax.legend(loc="upper right",bbox_to_anchor=(1.3,1.1)); fig.tight_layout(); save_figure(fig, "radar_comparison")
 
# Summary
md="## Key Findings\n\n| Indicator | Lilly | Novo |\n|---|---|---|\n"
for i in sdf.index: md+=f"| {i} | {sdf.loc[i,'Lilly']} | {sdf.loc[i,'Novo']} |\n"
with open("data/processed/summary.md","w") as f: f.write(md)
 
print("\n"+"="*60+"\n  ALL ANALYSES COMPLETE\n"+"="*60)
print("Outputs: data/processed/ and figures/")
