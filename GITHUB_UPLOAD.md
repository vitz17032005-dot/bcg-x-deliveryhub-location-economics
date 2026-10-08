# GitHub Upload

The code/docs can be published first. Upload the public source archives manually under:

`data/raw/archives/`

Required archives:
- `exchange_rate_to_usd.csv.zip`
- `exchange_rate_usd_to.csv.zip`
- `india_col_salary_longitudinal_2010_2024.csv.zip`
- `linkedin_role_market_extract.csv.zip`
- `linkedin_supporting_tables.zip`

The complete LinkedIn postings archive is better kept as a GitHub Release asset.

Run:

```bash
pip install -r requirements.txt
python src/run_model.py
pytest
```
