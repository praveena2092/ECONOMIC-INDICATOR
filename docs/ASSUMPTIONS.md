# Assumptions, data sources and limitations

## Data sources
| Panel | Source | Notes |
|---|---|---|
| Ticker – NIFTY BANK, NIFTY IT | **NSE India** `/api/allIndices` (cookie-primed session) | non-official-API; NSE may block cloud IPs or change the format – then the ticker goes stale/unavailable and says so |
| Ticker – SENSEX | BSE index, **non-NSE**: Yahoo Finance public chart endpoint | unofficial endpoint; labelled "(non-NSE)" |
| GDP growth India/World | World Bank `NY.GDP.MKTP.KD.ZG` | annual, lags 1+ year |
| Debt to GDP India/US | IMF DataMapper `GG_DEBT_GDP` (general government gross debt) | recent years may be preliminary; projection years are dropped |
| Exports / Imports | World Bank `NE.EXP.GNFS.CD`, `NE.IMP.GNFS.CD` (goods & services, USD) | trade balance = exports − imports |
| GST collections | Finance Ministry / PIB figures, curated CSV | no public API; FY23 reported as 18.07 or 18.08 by different outlets |
| Inflation | World Bank `FP.CPI.TOTL.ZG` (CPI, annual %) | RBI target 4% is a configured constant (RBI mandate 4% ± 2) |
| Government expenditure | Union Budget documents, curated CSV | only FY24 actual and FY25 revised estimate verified so far – extend `union_budget_expenditure.csv` |

## Design decisions where the Figma/image was open or inconsistent
* Figma could not be opened from the build environment; layout, colours and chart styles were derived from the
  reference image in the brief. **Open the Figma frame and compare spacing/typography before submitting**; the card
  illustrations are placeholder icons (export the real assets from Figma into `frontend/src`).
* The mock shows the same numbers in every panel; the app shows real data. Where a value is not published it is `---`.
* Arrows/colours follow the sign of the change (green ▲ up, red ▼ down); the mock shows green ▲ for negatives.
* Legend labels in the GST panel are correct (`GST Collections`, `Monthly Average`) instead of the mock's `Imports`.
* Debt-to-GDP x-axis shows years, not the mock's daily dates, because the sources are annual.
* "Ind vs US" card shows the **US ratio**; the India–US gap is not displayed.
* Fiscal-year series are labelled `FY25` etc.
* Visible controls: legend items toggle series, tooltips on charts, ticker pauses on hover, Sign out, Retry.

## Known limitations
* Collectors run inside the API process (single instance).
* Login rate limiting is per process.
* Upstream endpoints (NSE, Yahoo) are unofficial and could not be exercised from the development sandbox;
  parsers are unit-tested against sample payloads only.
* No refresh tokens: users sign in again after 60 minutes.
