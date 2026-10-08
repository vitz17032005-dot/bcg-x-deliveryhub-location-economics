# Technology Delivery Location Economics & Talent Market Optimizer — Public Data Edition

> A public-data decision system for comparing technology-delivery location economics using compensation, demand and FX signals.

## Decision question

> Which observed labor-market locations appear structurally attractive for technology delivery when compensation, role demand, data depth and FX stability are considered together?

## Data required

Upload the supplied compressed public archives under `data/raw/archives/`:

- `exchange_rate_to_usd.csv.zip`
- `exchange_rate_usd_to.csv.zip`
- `india_col_salary_longitudinal_2010_2024.csv.zip`
- `linkedin_role_market_extract.csv.zip`
- `linkedin_supporting_tables.zip`

The complete LinkedIn `postings.csv` archive is too large for ordinary Git and should be handled as a GitHub Release asset.

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

This is a relative public-market ranking, **not** an internal hub profitability forecast.

## Data interpretation

LinkedIn company-country is an observed labor-market signal. It should not be described as the physical location of a delivery center. India is additionally evaluated at city level using the dedicated salary / cost-of-living panel.

## Run

```bash
pip install -r requirements.txt
python src/run_model.py
pytest
```

No Kaggle credentials, API keys, KaggleHub or runtime dataset retrieval are required.
