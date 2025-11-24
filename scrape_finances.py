import math
from datetime import datetime
import os

import pandas as pd
import requests

# --- CONFIGURATION ---
SCHOOLS = [
    {"Name": "Princeton University", "EIN": "210634501"},
    {"Name": "Seton Hall University", "EIN": "221500645"},
    {"Name": "Stevens Institute of Technology", "EIN": "221487354"},
    {"Name": "Rider University", "EIN": "210650678"},
    {"Name": "TCNJ Foundation", "EIN": "222448189"},
    {"Name": "Destination College", "EIN": "222479262"}
]

CURRENT_YEAR = datetime.now().year
USER_AGENT = {'User-Agent': 'Mozilla/5.0 (compatible; NJSchoolTracker/1.0)'}

SCORECARD_ENDPOINT = "https://api.data.gov/ed/collegescorecard/v1/schools"
SCORECARD_FIELDS = [
    "id",
    "ope8_id",
    "school.name",
    "school.alias",
    "school.city",
    "school.school_url",
    "latest.student.size",
    "latest.admissions.admission_rate.overall",
    "latest.admissions.sat_scores.average.overall",
    "latest.admissions.act_scores.midpoint.cumulative",
    "latest.cost.tuition.in_state",
    "latest.cost.tuition.out_of_state",
    "latest.cost.attendance.academic_year",
    "latest.cost.average_net_price.overall",
    "latest.cost.roomboard.oncampus",
    "latest.cost.booksupply",
    "latest.cost.otherexpense.oncampus",
    "latest.cost.otherexpense.offcampus_with_family",
    "latest.aid.median_debt.completers.overall",
    "latest.earnings.10_yrs_after_entry.median"
]
SCORECARD_STATE = "NJ"
SCORECARD_PAGE_SIZE = 100
COLLEGE_COST_OUTPUT = "nj_college_costs.csv"

def fetch_nonprofit_data(ein):
    url = f"https://projects.propublica.org/nonprofits/api/v2/organizations/{ein}.json"
    try:
        # Pretend to be a browser to avoid blocking
        response = requests.get(url, headers=USER_AGENT, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('filings_with_data'):
                latest = data['filings_with_data'][0]
                return {
                    "Revenue": latest.get('totrevenue', 0),
                    "Expenses": latest.get('totfuncexpns', 0),
                    "Assets": latest.get('totassetsend', 0),
                    "Tax_Year": latest.get('tax_prd_yr', 'N/A'),
                    "Filing_PDF": latest.get('pdf_url', 'N/A')
                }
    except Exception as e:
        print(f"Error fetching {ein}: {e}")
    return None

def check_public_data():
    """Ping the external APIs we depend on and record their status."""
    status_messages = []

    try:
        params = {
            "school.state": SCORECARD_STATE,
            "per_page": 1,
            "page": 0,
            "fields": "id",
            "api_key": _resolve_scorecard_api_key()
        }
        response = requests.get(SCORECARD_ENDPOINT, params=params, timeout=10)
        response.raise_for_status()
        status_messages.append("AVAILABLE: College Scorecard API (cost + admissions)")
    except Exception as exc:
        status_messages.append(f"UNAVAILABLE: College Scorecard API ({exc})")

    if SCHOOLS:
        sample_ein = SCHOOLS[0]["EIN"]
        try:
            url = f"https://projects.propublica.org/nonprofits/api/v2/organizations/{sample_ein}.json"
            response = requests.get(url, headers=USER_AGENT, timeout=10)
            if response.status_code == 200:
                status_messages.append("AVAILABLE: ProPublica Nonprofit Explorer API")
            else:
                status_messages.append(
                    f"UNAVAILABLE: ProPublica Nonprofit Explorer (Status {response.status_code})"
                )
        except Exception as exc:
            status_messages.append(f"UNAVAILABLE: ProPublica Nonprofit Explorer ({exc})")

    return "\n".join(status_messages)


def _resolve_scorecard_api_key():
    key = os.getenv("SCORECARD_API_KEY")
    if key:
        return key
    if not getattr(_resolve_scorecard_api_key, "_warned", False):
        print("Using College Scorecard DEMO_KEY; set SCORECARD_API_KEY for higher rate limits.")
        _resolve_scorecard_api_key._warned = True
    return "DEMO_KEY"


def fetch_scorecard_rows(state=SCORECARD_STATE):
    """Pull every New Jersey institution available in the College Scorecard API."""
    rows = []
    page = 0
    total_pages = None
    per_page = SCORECARD_PAGE_SIZE

    while True:
        params = {
            "school.state": state,
            "per_page": per_page,
            "page": page,
            "fields": ",".join(SCORECARD_FIELDS),
            "api_key": _resolve_scorecard_api_key()
        }

        try:
            response = requests.get(SCORECARD_ENDPOINT, params=params, timeout=20)
            response.raise_for_status()
        except Exception as exc:
            print(f"Failed to fetch College Scorecard page {page}: {exc}")
            break

        payload = response.json()
        page_rows = payload.get("results", [])
        if not page_rows:
            break
        rows.extend(page_rows)

        metadata = payload.get("metadata", {})
        total = metadata.get("total")
        per_page = metadata.get("per_page", per_page)
        if total and total_pages is None:
            total_pages = math.ceil(total / per_page)

        page += 1
        if total_pages is not None and page >= total_pages:
            break
        if total_pages is None and len(page_rows) < per_page:
            break

    return rows


def _to_percent(value):
    if value in (None, ""):
        return None
    try:
        return round(float(value) * 100, 2)
    except (TypeError, ValueError):
        return None


def _clean_number(value):
    if value in (None, ""):
        return None
    try:
        return round(float(value), 2)
    except (TypeError, ValueError):
        return value


def normalize_scorecard_rows(rows):
    table = []
    for record in rows:
        table.append({
            "School Name": record.get("school.name"),
            "City": record.get("school.city"),
            "Website": record.get("school.school_url"),
            "Enrollment": record.get("latest.student.size"),
            "Admission Rate (%)": _to_percent(record.get("latest.admissions.admission_rate.overall")),
            "Average SAT": _clean_number(record.get("latest.admissions.sat_scores.average.overall")),
            "Average ACT": _clean_number(record.get("latest.admissions.act_scores.midpoint.cumulative")),
            "Tuition (In State)": _clean_number(record.get("latest.cost.tuition.in_state")),
            "Tuition (Out of State)": _clean_number(record.get("latest.cost.tuition.out_of_state")),
            "Published Cost (Academic Year)": _clean_number(record.get("latest.cost.attendance.academic_year")),
            "Average Net Price": _clean_number(record.get("latest.cost.average_net_price.overall")),
            "Room & Board (On Campus)": _clean_number(record.get("latest.cost.roomboard.oncampus")),
            "Books & Supplies": _clean_number(record.get("latest.cost.booksupply")),
            "Other On-Campus Expenses": _clean_number(record.get("latest.cost.otherexpense.oncampus")),
            "Other Off-Campus w/Family": _clean_number(record.get("latest.cost.otherexpense.offcampus_with_family")),
            "Median Debt at Graduation": _clean_number(record.get("latest.aid.median_debt.completers.overall")),
            "Median Earnings 10y After Entry": _clean_number(record.get("latest.earnings.10_yrs_after_entry.median")),
            "IPEDS ID": record.get("id"),
            "OPE8 ID": record.get("ope8_id")
        })
    return table


def collect_college_costs(state=SCORECARD_STATE, output_path=COLLEGE_COST_OUTPUT):
    """Build a student-focused cost-of-attendance CSV for all NJ colleges."""
    print(f"Fetching College Scorecard cost data for {state} institutions...")
    rows = fetch_scorecard_rows(state)
    if not rows:
        print("No college cost data captured; skipping CSV export.")
        return

    normalized = normalize_scorecard_rows(rows)
    df = pd.DataFrame(normalized).sort_values("School Name")
    df.to_csv(output_path, index=False)
    print(f"Saved student cost guide to {output_path} ({len(df)} schools).")

def collect_nonprofit_financials(output_path="nj_school_finances.csv"):
    print("Gathering Form 990 summaries for configured EINs...")
    results = []

    for school in SCHOOLS:
        print(f"  - {school['Name']}")
        financials = fetch_nonprofit_data(school['EIN'])

        row = {
            "School Name": school['Name'],
            "EIN": school['EIN'],
            "Last Updated": datetime.now().strftime("%Y-%m-%d")
        }

        if financials:
            row.update(financials)
        else:
            row.update({
                "Revenue": 0,
                "Expenses": 0,
                "Assets": 0,
                "Tax_Year": "Error",
                "Filing_PDF": "N/A"
            })

        results.append(row)

    if not results:
        print("No EINs configured; skipping nonprofit snapshot.")
        return

    df = pd.DataFrame(results)
    cols = [
        "School Name",
        "Revenue",
        "Expenses",
        "Assets",
        "Tax_Year",
        "Last Updated",
        "EIN",
        "Filing_PDF"
    ]
    df = df.reindex(columns=cols)
    df.to_csv(output_path, index=False)
    print(f"Saved nonprofit snapshot to {output_path}")


def write_public_status():
    public_status = check_public_data()
    with open("public_data_status.txt", "w") as f:
        f.write(f"Last Checked: {datetime.now()}\n\n")
        f.write(public_status)
    print("Recorded upstream API status.")


def main():
    print("--- Starting NJ college data refresh ---")
    collect_nonprofit_financials()
    collect_college_costs(state=SCORECARD_STATE)
    write_public_status()

if __name__ == "__main__":
    main()
