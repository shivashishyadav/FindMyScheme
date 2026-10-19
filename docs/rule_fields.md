# Supported rule fields

| Field | Type | Example value |
|---|---|---|
| age | number | 18 |
| annual_income | number (INR) | 250000 |
| land_acres | number | 0 |
| occupation | choice | "farmer" |
| state | choice | "uttar pradesh" |
| gender | choice | "female" |
| category | choice | "obc" |
| is_income_tax_payer | boolean | false |

## Conventions
- All text values are lowercase.
- Income is always stored as a plain number in INR (2.5 lakh = 250000).
- All rules of a scheme are combined with AND. For OR, use `in` with a list.
- Anything not in this list is shown to users as "check the official portal".