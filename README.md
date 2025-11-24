# school-finances
Data Attribution & Disclaimer

Non-profit financial data is sourced from the ProPublica Nonprofit Explorer API.

Public school budget, tuition, and cost data are sourced from the NJ Department of Education Indicator 1 workbooks.

This tool is for educational and research purposes only. I do not claim ownership of the underlying data.

## Outputs

- `nj_school_finances.csv`: latest IRS Form 990 aggregates (revenue, expenses, assets) for configured EINs.
- `nj_tuition_costs.csv`: merged tuition and associated cost categories for the current and prior DOE Guide years. Every worksheet from the Indicator 1 workbook is preserved so no cost columns are discarded.
