-- 20261015000002_seed_indicators.sql
-- Indicator catalogue (metadata only; numbers come from collectors). Idempotent upsert.

insert into indicators (code, name, unit, frequency, source_name, source_url, is_nse, stale_after_seconds, notes) values
 ('ticker',          'Market ticker',                   'points', 'intraday', 'NSE India (allIndices); SENSEX via Yahoo Finance', 'https://www.nseindia.com/market-data/live-market-indices', true, 900, 'SENSEX is a BSE index, not published by NSE.'),
 ('gdp_growth',      'GDP growth (annual %)',           '%',      'annual',   'World Bank (NY.GDP.MKTP.KD.ZG)', 'https://data.worldbank.org/indicator/NY.GDP.MKTP.KD.ZG', false, 259200, null),
 ('debt_gdp',        'General government gross debt, % of GDP', '%', 'annual', 'IMF DataMapper (GG_DEBT_GDP)', 'https://www.imf.org/external/datamapper/GG_DEBT_GDP', false, 259200, 'Recent years can be preliminary IMF estimates.'),
 ('exports',         'Exports of goods and services',   'USD',    'annual',   'World Bank (NE.EXP.GNFS.CD)', 'https://data.worldbank.org/indicator/NE.EXP.GNFS.CD', false, 259200, null),
 ('imports',         'Imports of goods and services',   'USD',    'annual',   'World Bank (NE.IMP.GNFS.CD)', 'https://data.worldbank.org/indicator/NE.IMP.GNFS.CD', false, 259200, null),
 ('gst_collections', 'Gross GST collections',           'INR lakh crore', 'annual', 'Ministry of Finance / PIB (curated dataset)', 'https://pib.gov.in', false, 259200, 'No public API; loaded from backend/data/curated/gst_collections.csv.'),
 ('inflation',       'Inflation, CPI (annual %)',       '%',      'annual',   'World Bank (FP.CPI.TOTL.ZG)', 'https://data.worldbank.org/indicator/FP.CPI.TOTL.ZG', false, 259200, null),
 ('gov_expenditure', 'Union Government expenditure',    'INR lakh crore', 'annual', 'Union Budget documents (curated dataset)', 'https://www.indiabudget.gov.in', false, 259200, 'No public API; loaded from backend/data/curated/union_budget_expenditure.csv.')
on conflict (code) do update set
    name = excluded.name, unit = excluded.unit, frequency = excluded.frequency,
    source_name = excluded.source_name, source_url = excluded.source_url, is_nse = excluded.is_nse,
    stale_after_seconds = excluded.stale_after_seconds, notes = excluded.notes;
