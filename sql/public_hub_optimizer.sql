-- Public-data hub screening views.
SELECT employer_country, postings, median_salary_usd, role_count, cost_score, demand_score, fx_stability_score, decision_score
FROM hub_location_scorecard
ORDER BY decision_score DESC;

SELECT employer_country, role_family, postings, median_salary_usd, salary_observations
FROM hub_role_market_economics
ORDER BY employer_country, postings DESC;
