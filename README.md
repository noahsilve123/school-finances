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

## Automation

- `.github/workflows/daily_scrape.yml` runs every morning to keep the IRS snapshot and availability log fresh. It also commits the regenerated `nj_college_costs.csv` if the data changes.
- `.github/workflows/monthly_student_costs.yml` runs at 09:00 UTC on the first of each month so prospective students always have a current cost-of-attendance file. You can trigger it manually via the **Run workflow** button if you need an ad-hoc refresh.

### Supplying a College Scorecard API key in Actions

Create a repository secret named `SCORECARD_API_KEY` (GitHub repo → Settings → Secrets and variables → Actions). To have the workflows use it, add the following step before `Run scraper` in the workflow file:

```yaml
			- name: Export Scorecard API key
				run: echo "SCORECARD_API_KEY=${{ secrets.SCORECARD_API_KEY }}" >> $GITHUB_ENV
```

If the secret is missing the script automatically uses `DEMO_KEY`, but those calls are severely rate-limited.
