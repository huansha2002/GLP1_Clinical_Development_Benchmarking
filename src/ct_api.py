"""
ClinicalTrials.gov v2 API wrapper.
"""
import time
import requests
import pandas as pd
from tqdm import tqdm
from src.config import CT_API_BASE, CT_PAGE_SIZE
 
 
def _flatten_study(study):
    proto = study.get("protocolSection", {})
    ident = proto.get("identificationModule", {})
    status = proto.get("statusModule", {})
    sponsor = proto.get("sponsorCollaboratorsModule", {})
    design = proto.get("designModule", {})
    arms = proto.get("armsInterventionsModule", {})
    conditions = proto.get("conditionsModule", {})
    outcomes = proto.get("outcomesModule", {})
    contacts = proto.get("contactsLocationsModule", {})
 
    lead = sponsor.get("leadSponsor", {})
    collabs = sponsor.get("collaborators", [])
    design_info = design.get("designInfo", {})
    enrollment_info = design.get("enrollmentInfo", {})
    phases = design.get("phases", [])
    phase_str = "|".join(phases) if phases else "NA"
 
    interventions = arms.get("interventions", [])
    interv_names = [i.get("name", "") for i in interventions]
    interv_types = [i.get("type", "") for i in interventions]
    conds = conditions.get("conditions", [])
 
    primary_oc = outcomes.get("primaryOutcomes", [])
    primary_measures = [o.get("measure", "") for o in primary_oc]
    primary_timeframes = [o.get("timeFrame", "") for o in primary_oc]
    secondary_oc = outcomes.get("secondaryOutcomes", [])
    secondary_measures = [o.get("measure", "") for o in secondary_oc]
 
    locations = contacts.get("locations", [])
    countries = list(set(loc.get("country", "") for loc in locations if loc.get("country")))
    n_sites = len(locations)
 
    sds = status.get("startDateStruct", {})
    pcs = status.get("primaryCompletionDateStruct", {})
    cds = status.get("completionDateStruct", {})
    rfs = status.get("resultsFirstPostDateStruct", {})
 
    return {
        "nct_id": ident.get("nctId", ""),
        "brief_title": ident.get("briefTitle", ""),
        "official_title": ident.get("officialTitle", ""),
        "acronym": ident.get("acronym", ""),
        "overall_status": status.get("overallStatus", ""),
        "why_stopped": status.get("whyStopped", ""),
        "start_date": sds.get("date", ""),
        "start_date_type": sds.get("type", ""),
        "primary_completion_date": pcs.get("date", ""),
        "primary_completion_type": pcs.get("type", ""),
        "completion_date": cds.get("date", ""),
        "completion_date_type": cds.get("type", ""),
        "results_first_post_date": rfs.get("date", ""),
        "lead_sponsor": lead.get("name", ""),
        "lead_sponsor_class": lead.get("class", ""),
        "collaborators": "|".join(c.get("name", "") for c in collabs),
        "study_type": design.get("studyType", ""),
        "phases": phase_str,
        "allocation": design_info.get("allocation", ""),
        "intervention_model": design_info.get("interventionModel", ""),
        "primary_purpose": design_info.get("primaryPurpose", ""),
        "masking": design_info.get("maskingInfo", {}).get("masking", ""),
        "enrollment_count": enrollment_info.get("count", None),
        "enrollment_type": enrollment_info.get("type", ""),
        "intervention_names": "|".join(interv_names),
        "intervention_types": "|".join(interv_types),
        "conditions": "|".join(conds),
        "primary_outcome_measures": "|".join(primary_measures),
        "primary_outcome_timeframes": "|".join(primary_timeframes),
        "secondary_outcome_measures": "|".join(secondary_measures),
        "location_countries": "|".join(sorted(countries)),
        "n_sites": n_sites,
    }
 
 
def search_studies(query_expr, page_size=CT_PAGE_SIZE, delay=0.4):
    all_rows = []
    next_token = None
    while True:
        params = {"query.term": query_expr, "pageSize": page_size, "format": "json"}
        if next_token:
            params["pageToken"] = next_token
        resp = requests.get(CT_API_BASE, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        studies = data.get("studies", [])
        if not studies:
            break
        for s in studies:
            all_rows.append(_flatten_study(s))
        next_token = data.get("nextPageToken")
        if not next_token:
            break
        time.sleep(delay)
    return all_rows
 
 
def fetch_glp1_trials():
    from src.config import GLP1_DRUGS, SPONSORS
    all_search_terms = set()
    for drug, info in GLP1_DRUGS.items():
        all_search_terms.add(drug)
        for brand in info["brands"]:
            all_search_terms.add(brand)
 
    all_rows = []
    seen_nct = set()
    for term in tqdm(sorted(all_search_terms), desc="Fetching trials"):
        query = f"AREA[InterventionName]{term}"
        rows = search_studies(query)
        for r in rows:
            if r["nct_id"] not in seen_nct:
                seen_nct.add(r["nct_id"])
                all_rows.append(r)
 
    df = pd.DataFrame(all_rows)
    if df.empty:
        return df
 
    sponsor_names = set()
    for sp_info in SPONSORS.values():
        for name in sp_info["api_terms"]:
            sponsor_names.add(name.lower())
 
    mask = df["lead_sponsor"].str.lower().isin(sponsor_names)
    for idx, row in df.iterrows():
        if not mask[idx]:
            collabs = str(row.get("collaborators", "")).lower()
            for sn in sponsor_names:
                if sn in collabs:
                    mask[idx] = True
                    break
 
    df = df[mask].copy().reset_index(drop=True)
 
    def _norm(name):
        nl = name.lower()
        for sp, info in SPONSORS.items():
            for t in info["api_terms"]:
                if t.lower() in nl:
                    return sp
        return name
    df["sponsor_normalized"] = df["lead_sponsor"].apply(_norm)
 
    def _tag(interv_str):
        il = str(interv_str).lower()
        matched = []
        for drug, info in GLP1_DRUGS.items():
            check = [drug] + [b.lower() for b in info["brands"]]
            for n in check:
                if n.lower() in il:
                    matched.append(drug)
                    break
        return "|".join(sorted(set(matched))) if matched else ""
    df["glp1_drugs_matched"] = df["intervention_names"].apply(_tag)
 
    return df
