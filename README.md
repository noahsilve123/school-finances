# school-finances
Data Attribution & Disclaimer

Non-profit financial data is sourced from the ProPublica Nonprofit Explorer API.

Student-facing tuition, room & board, and related cost figures are sourced from the U.S. Department of Education College Scorecard API.

This tool is for educational and research purposes only. I do not claim ownership of the underlying data.

## Outputs

- `nj_school_finances.csv`: latest IRS Form 990 aggregates (revenue, expenses, assets) for configured EINs.
- `nj_college_costs.csv`: College Scorecard data for every New Jersey institution, including admission rate, tuition (in/out-of-state), published cost of attendance, average net price, room & board, books, miscellaneous expenses, and graduate outcomes.
- `public_data_status.txt`: quick health check for the upstream APIs so you know when a data source is down.

## Configuration

- Set the `SCORECARD_API_KEY` environment variable for higher College Scorecard rate limits. When it is not provided the script falls back to the public `DEMO_KEY`, which is heavily throttled.
