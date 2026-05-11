"""
Configuration for Cross-Company Clinical Development Efficiency Benchmarking.
To extend this framework to another therapeutic area, modify the parameters below.
"""

SPONSORS = {
    "Eli Lilly": {
        "api_terms": ["Eli Lilly", "Eli Lilly and Company"],
        "short": "Lilly",
        "color": "#D52B1E",
    },
    "Novo Nordisk": {
        "api_terms": ["Novo Nordisk", "Novo Nordisk A/S"],
        "short": "Novo",
        "color": "#00205B",
    },
}

GLP1_DRUGS = {
    "tirzepatide":  {"sponsor": "Eli Lilly",    "brands": ["Mounjaro", "Zepbound"]},
    "dulaglutide":  {"sponsor": "Eli Lilly",    "brands": ["Trulicity"]},
    "exenatide":    {"sponsor": "Eli Lilly",    "brands": ["Byetta", "Bydureon"]},
    "orforglipron": {"sponsor": "Eli Lilly",    "brands": []},
    "retatrutide":  {"sponsor": "Eli Lilly",    "brands": []},
    "semaglutide":  {"sponsor": "Novo Nordisk", "brands": ["Ozempic", "Wegovy", "Rybelsus"]},
    "liraglutide":  {"sponsor": "Novo Nordisk", "brands": ["Victoza", "Saxenda"]},
    "cagrilintide": {"sponsor": "Novo Nordisk", "brands": []},
}

CT_API_BASE = "https://clinicaltrials.gov/api/v2/studies"
CT_PAGE_SIZE = 100

PHASE_ORDER = ["EARLY_PHASE1", "PHASE1", "PHASE1_PHASE2", "PHASE2",
               "PHASE2_PHASE3", "PHASE3", "PHASE4", "NA"]
PHASE_LABELS = {
    "EARLY_PHASE1": "Early Phase 1",
    "PHASE1": "Phase 1",
    "PHASE1_PHASE2": "Phase 1/2",
    "PHASE2": "Phase 2",
    "PHASE2_PHASE3": "Phase 2/3",
    "PHASE3": "Phase 3",
    "PHASE4": "Phase 4",
    "NA": "N/A",
}
