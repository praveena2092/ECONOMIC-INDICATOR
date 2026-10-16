# Curated datasets

Indicators with no public API are loaded from these CSVs by `app/collectors/curated.py`
(at startup and on every macro refresh). Values are in INR lakh crore.

* `gst_collections.csv` – gross GST collections per fiscal year, from Finance Ministry / PIB statements
  as reported in the press (FY23 appears as 18.07 or 18.08 depending on the outlet – verify against PIB).
* `union_budget_expenditure.csv` – Union Budget "actuals" and "revised estimates". Only years that were
  verified are included; add earlier years from the Budget at a Glance document. Gaps are shown as `---`.

Never add a number you cannot cite – the dashboard displays `basis` and the source for every figure.
