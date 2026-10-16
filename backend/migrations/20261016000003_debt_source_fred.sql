update indicators set
    name = 'General government gross debt, % of GDP',
    source_name = 'IMF World Economic Outlook via FRED',
    source_url = 'https://fred.stlouisfed.org/series/GGGDTAINA188N',
    notes = 'IMF WEO data republished by FRED; latest year can lag by 1-2 years.'
where code = 'debt_gdp';