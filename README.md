# Technology Delivery Location Economics & Talent Market Optimizer — Public Data Edition

> A public-data decision system for comparing technology-delivery location economics using compensation, demand and FX signals.

## Decision question

> Which observed labor-market locations appear structurally attractive for technology delivery when compensation, role demand, data depth and FX stability are considered together?

## Compressed public inputs

- `data/raw/archives/exchange_rate_to_usd.csv.zip` — supplied Kaggle/IMF source.
- `data/raw/archives/exchange_rate_usd_to.csv.zip` — supplied Kaggle/IMF source.
- `data/raw/archives/india_col_salary_longitudinal_2010_2024.csv.zip` — supplied Kaggle city salary / cost-of-living panel.
- `data/raw/archives/linkedin_role_market_extract.csv.zip` — exact source-derived technology-role extract from the supplied Kaggle `postings.csv`.
- `data/raw/archives/linkedin_supporting_tables.zip` — original smaller LinkedIn CSVs.

The complete LinkedIn `postings.csv` is preserved as a GitHub Release asset rather than tracked in ordinary Git. See `GITHUB_RELEASE_ASSETS.md`.

## Model

```text
Observed job demand + compensation + FX
                ↓
        role classification
                ↓
        USD normalization
                ↓
     country / role economics
                ↓
       weighted scorecard
                ↓
       location shortlist
```

### Scorecard

- 55% compensation advantage
- 20% role-demand depth
- 15% salary-data depth
- 10% FX stability

The score is a relative public-market ranking, **not** an internal hub profitability forecast.

## Data interpretation

LinkedIn company-country is used as an observed labor-market signal. It should not be described as the physical location of a delivery center. India is additionally evaluated at city level using the dedicated salary / cost-of-living panel.

## Run

```bash
pip install -r requirements.txt
python src/run_model.py
pytest
```

No Kaggle credentials, APIs or retrieval scripts are required.