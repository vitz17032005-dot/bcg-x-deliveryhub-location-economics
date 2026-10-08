from pathlib import Path
import json
import numpy as np
import pandas as pd
import zipfile

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed"
CFG = json.loads((ROOT / "config" / "source_config.json").read_text(encoding="utf-8"))

def read_csv_from_zip(zip_path: Path, csv_name: str, **kwargs):
    with zipfile.ZipFile(zip_path) as z:
        if csv_name not in z.namelist():
            raise FileNotFoundError(f"{csv_name} not found in {zip_path}")
        with z.open(csv_name) as fh:
            return pd.read_csv(fh, **kwargs)

COUNTRY_NAMES = {
    "US":"United States","GB":"United Kingdom","CA":"Canada","IN":"India","DE":"Germany","FR":"France",
    "CH":"Switzerland","SE":"Sweden","NL":"Netherlands","SG":"Singapore","AU":"Australia","ES":"Spain",
    "IE":"Ireland","DK":"Denmark","NO":"Norway","BR":"Brazil","JP":"Japan","CN":"China","FI":"Finland",
    "IL":"Israel","AE":"United Arab Emirates","MX":"Mexico","PK":"Pakistan","VN":"Vietnam","LU":"Luxembourg"
}

CURRENCY = {
    "United States":"US_DOLLAR_TO_USD","United Kingdom":"UK_POUND_TO_USD","Canada":"CANADIAN_DOLLAR_TO_USD",
    "India":"INDIAN_RUPEE_TO_USD","Germany":"EURO_TO_USD","France":"EURO_TO_USD","Switzerland":"SWISS_FRANC_TO_USD",
    "Sweden":"SWEDISH_KRONA_TO_USD","Netherlands":"EURO_TO_USD","Singapore":"SINGAPORE_DOLLAR_TO_USD",
    "Australia":"AUSTRALIAN_DOLLAR_TO_USD","Spain":"EURO_TO_USD","Ireland":"EURO_TO_USD","Denmark":"DANISH_KRONE_TO_USD",
    "Norway":"NORWEGIAN_KRONE_TO_USD","Brazil":"BRAZILIAN_REAL_TO_USD","Japan":"JAPANESE_YEN_TO_USD",
    "China":"CHINESE_YUAN_TO_USD","Finland":"EURO_TO_USD","Israel":"ISRAELI_NEW_SHEKEL_TO_USD",
    "Mexico":"MEXICAN_PESO_TO_USD","Pakistan":"PAKISTANI_RUPEE_TO_USD","Vietnam":"VIETNAMESE_DONG_TO_USD",
    "Luxembourg":"EURO_TO_USD"
}

def load_jobs():
    p = RAW / "archives" / "linkedin_role_market_extract.csv.zip"
    if not p.exists():
        raise FileNotFoundError(f"Missing {p}")
    return read_csv_from_zip(p, "linkedin_role_market_extract.csv", low_memory=False)

def load_fx():
    p = RAW / "archives" / "exchange_rate_to_usd.csv.zip"
    if not p.exists():
        raise FileNotFoundError(f"Missing {p}")
    df = read_csv_from_zip(p, "exchange_rate_to_usd.csv").rename(columns=lambda c: str(c).strip())
    df = df.rename(columns={df.columns[0]:"date"})
    vals = [c for c in df.columns if c != "date"]
    out = df.melt(id_vars=["date"],value_vars=vals,var_name="currency",value_name="rate_to_usd")
    out["date"] = pd.to_datetime(out["date"],errors="coerce")
    out["rate_to_usd"] = pd.to_numeric(out["rate_to_usd"],errors="coerce")
    return out.dropna(subset=["date","rate_to_usd"])

def load_india():
    p = RAW / "archives" / "india_col_salary_longitudinal_2010_2024.csv.zip"
    if not p.exists():
        raise FileNotFoundError(f"Missing {p}")
    return read_csv_from_zip(p,"india_col_salary_longitudinal_2010_2024.csv")

def role_family(title):
    text=str(title).lower()
    for role,kws in CFG["role_keywords"].items():
        if any(k in text for k in kws):
            return role
    return "Other"

def normalize_salary_to_usd(jobs,fx):
    x=jobs.copy()
    x["role_family"]=x["title"].map(role_family)
    lo=pd.to_numeric(x["min_salary"],errors="coerce")
    med=pd.to_numeric(x["med_salary"],errors="coerce")
    hi=pd.to_numeric(x["max_salary"],errors="coerce")
    x["salary_local_annual"]=med.fillna((lo+hi)/2)
    mult=x["pay_period"].fillna("").astype(str).str.upper().map({"YEARLY":1,"MONTHLY":12,"HOURLY":2080}).fillna(1)
    x["salary_local_annual"]*=mult
    latest=fx.sort_values("date").groupby("currency",as_index=False).tail(1)
    lookup=dict(zip(latest["currency"].astype(str).str.upper(),latest["rate_to_usd"].astype(float)))
    aliases={"USD":"US_DOLLAR_TO_USD","GBP":"UK_POUND_TO_USD","INR":"INDIAN_RUPEE_TO_USD","EUR":"EURO_TO_USD","CAD":"CANADIAN_DOLLAR_TO_USD","PLN":"POLISH_ZLOTY_TO_USD","MXN":"MEXICAN_PESO_TO_USD","CHF":"SWISS_FRANC_TO_USD","SEK":"SWEDISH_KRONA_TO_USD","NOK":"NORWEGIAN_KRONE_TO_USD","DKK":"DANISH_KRONE_TO_USD","CNY":"CHINESE_YUAN_TO_USD","JPY":"JAPANESE_YEN_TO_USD","SGD":"SINGAPORE_DOLLAR_TO_USD","AUD":"AUSTRALIAN_DOLLAR_TO_USD","BRL":"BRAZILIAN_REAL_TO_USD"}
    x["currency_key"]=x["currency"].fillna("").astype(str).str.upper().map(aliases).fillna(x["currency"].fillna("").astype(str).str.upper())
    x["fx_rate_to_usd"]=x["currency_key"].map(lookup)
    r=x["fx_rate_to_usd"]
    x["salary_usd_annual"]=np.where(r.isna(),np.nan,np.where(r>1,x["salary_local_annual"]/r,x["salary_local_annual"]*r))
    x["employer_country"]=x["company_country"].map(COUNTRY_NAMES).fillna("Unknown")
    return x

def score_hubs(jobs,fx):
    eligible=jobs[jobs["role_family"].isin(CFG["hub_candidate_logic"]["eligible_roles"])].copy()
    eligible=eligible[eligible["employer_country"].ne("Unknown")]
    agg=eligible.groupby(["employer_country","role_family"],dropna=False).agg(postings=("job_id","nunique"),median_salary_usd=("salary_usd_annual","median"),salary_observations=("salary_usd_annual",lambda s:int(s.notna().sum()))).reset_index()
    min_postings=int(CFG["hub_candidate_logic"]["min_postings"])
    total=agg.groupby("employer_country",as_index=False)["postings"].sum().rename(columns={"postings":"country_postings"})
    agg=agg.merge(total,on="employer_country",how="left")
    agg["demand_share"]=agg["postings"]/agg["country_postings"]
    country=agg.groupby("employer_country",as_index=False).agg(postings=("postings","sum"),median_salary_usd=("median_salary_usd","median"),salary_observations=("salary_observations","sum"),role_count=("role_family","nunique"))
    country=country[country["postings"]>=min_postings].copy()
    country["cost_score"]=1-country["median_salary_usd"].rank(pct=True,ascending=False)
    country["demand_score"]=country["postings"].rank(pct=True,ascending=True)
    country["salary_depth_score"]=country["salary_observations"].rank(pct=True,ascending=True)
    fx=fx.sort_values(["currency","date"]).copy()
    fx["ret"]=fx.groupby("currency")["rate_to_usd"].pct_change()
    fx_std=fx.groupby("currency")["ret"].std()
    country["currency"]=country["employer_country"].map(CURRENCY)
    country["fx_std"]=country["currency"].map(fx_std)
    country["fx_stability_score"]=1-country["fx_std"].rank(pct=True,ascending=True).fillna(0.5)
    w=CFG["weights"]
    country["decision_score"]=country["cost_score"]*w["cost"]+country["demand_score"]*w["demand"]+country["salary_depth_score"]*w["salary_depth"]+country["fx_stability_score"]*w["fx_stability"]
    return country.sort_values("decision_score",ascending=False),agg.sort_values(["employer_country","postings"],ascending=[True,False])

def india_city_panel(india,fx):
    x=india.copy()
    x["year"]=pd.to_numeric(x["year"],errors="coerce")
    x["avg_salary_inr_monthly"]=pd.to_numeric(x["avg_salary_gross_inr_monthly"],errors="coerce")
    inr=fx[fx["currency"].astype(str).str.upper().eq("INDIAN_RUPEE_TO_USD")].copy()
    inr["year"]=inr["date"].dt.year
    annual=inr.groupby("year",as_index=False)["rate_to_usd"].mean().rename(columns={"rate_to_usd":"avg_inr_per_usd"})
    x=x.merge(annual,on="year",how="left")
    x["avg_salary_usd_monthly"]=x["avg_salary_inr_monthly"]/x["avg_inr_per_usd"]
    x["salary_growth_yoy"]=x.groupby("city")["avg_salary_usd_monthly"].pct_change()
    cols=[c for c in ["year","city","state","city_tier","avg_salary_inr_monthly","avg_salary_usd_monthly","cost_of_living_index","affordability_ratio","salary_growth_yoy"] if c in x]
    return x[cols]

def run():
    OUT.mkdir(parents=True,exist_ok=True)
    fx=load_fx()
    jobs=normalize_salary_to_usd(load_jobs(),fx)
    india=load_india()
    hub_scores,role_scores=score_hubs(jobs,fx)
    city=india_city_panel(india,fx)
    jobs.to_csv(OUT/"fact_job_market.csv",index=False)
    fx.to_csv(OUT/"fact_fx_daily.csv",index=False)
    hub_scores.to_csv(OUT/"location_economics_scorecard.csv",index=False)
    role_scores.to_csv(OUT/"location_role_market_economics.csv",index=False)
    city.to_csv(OUT/"india_city_salary_panel.csv",index=False)
    metadata={"synthetic_operational_data":False,"linkedin_source":"source-derived extract from supplied Kaggle postings.csv","linkedin_extract_rows":int(len(jobs)),"note":"Location scores use observed employer-country labor-market signals; they are not internal hub profitability or capacity forecasts."}
    (OUT/"build_metadata.json").write_text(json.dumps(metadata,indent=2),encoding="utf-8")
    print("Public-data location optimizer built. No synthetic business records used.")

if __name__=="__main__":
    run()
