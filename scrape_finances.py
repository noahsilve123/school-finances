import requests
import pandas as pd
from datetime import datetime
from pathlib import Path
import os

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
PUBLIC_DATA_URLS = [
    f"https://www.nj.gov/education/guide/{CURRENT_YEAR}/excel/indicator1.xls",
    f"https://www.nj.gov/education/guide/{CURRENT_YEAR - 1}/excel/indicator1.xls"
]
DOE_INDICATOR_TEMPLATE = "https://www.nj.gov/education/guide/{year}/excel/indicator1.xls"
DOE_COST_OUTPUT = "nj_tuition_costs.csv"
DOE_YEARS = [CURRENT_YEAR, CURRENT_YEAR - 1]
DATA_DIR = Path("data")
USER_AGENT = {'User-Agent': 'Mozilla/5.0 (compatible; NJSchoolTracker/1.0)'}

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
    status_messages = []
    for url in PUBLIC_DATA_URLS:
        try:
            response = requests.head(url, timeout=5)
            if response.status_code == 200:
                status_messages.append(f"AVAILABLE: {url}")
            else:
                status_messages.append(f"NOT RELEASED YET: {url} (Status {response.status_code})")
        except:
            status_messages.append(f"ERROR CHECKING: {url}")
    return "\n".join(status_messages)


def download_indicator_workbook(year):
    """Download the DOE tuition workbook for a given year."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    url = DOE_INDICATOR_TEMPLATE.format(year=year)
    destination = DATA_DIR / f"indicator1_{year}.xls"

    try:
        response = requests.get(url, headers=USER_AGENT, timeout=20)
        response.raise_for_status()
    except Exception as exc:
        print(f"Failed to download tuition workbook for {year}: {exc}")
        return None

    with open(destination, "wb") as handle:
        handle.write(response.content)

    return destination


def parse_indicator_workbook(path_obj, year):
    """Load every sheet from the workbook so no cost categories are lost."""
    if path_obj is None or not path_obj.exists():
        return None

    suffix = path_obj.suffix.lower()
    engine = "openpyxl" if suffix == ".xlsx" else "xlrd"

    try:
        sheets = pd.read_excel(path_obj, sheet_name=None, engine=engine)
    except Exception as exc:
        print(f"Failed to parse workbook for {year}: {exc}")
        return None

    frames = []
    for sheet_name, sheet_df in sheets.items():
        cleaned = sheet_df.dropna(how='all')
        cleaned = cleaned.loc[:, cleaned.notna().any()]  # remove empty columns
        if cleaned.empty:
            continue
        cleaned.insert(0, "DOE Sheet", str(sheet_name).strip())
        cleaned.insert(0, "DOE School Year", year)
        frames.append(cleaned)

    if not frames:
        return None

    return pd.concat(frames, ignore_index=True)


def collect_tuition_costs(years, output_path=DOE_COST_OUTPUT):
    """Persist tuition plus cost-of-attendance information for every requested year."""
    tuition_frames = []
    for year in years:
        workbook_path = download_indicator_workbook(year)
        parsed = parse_indicator_workbook(workbook_path, year)
        if parsed is not None:
            tuition_frames.append(parsed)
            print(f"Captured tuition workbook for {year} ({len(parsed)} rows).")

    if not tuition_frames:
        print("No tuition cost data captured; skipping CSV export.")
        return

    combined = pd.concat(tuition_frames, ignore_index=True)
    combined.to_csv(output_path, index=False)
    print(f"Saved tuition and cost data to {output_path}")

def main():
    print("--- Starting Financial Scrape ---")
    results = []
    
    for school in SCHOOLS:
        print(f"Fetching data for {school['Name']}...")
        financials = fetch_nonprofit_data(school['EIN'])
        
        row = {
            "School Name": school['Name'],
            "EIN": school['EIN'],
            "Last Updated": datetime.now().strftime("%Y-%m-%d")
        }
        
        if financials:
            row.update(financials)
        else:
            # Added Filing_PDF here to prevent crashes
            row.update({"Revenue": 0, "Expenses": 0, "Assets": 0, "Tax_Year": "Error", "Filing_PDF": "N/A"})
            
        results.append(row)

    df = pd.DataFrame(results)
    cols = ["School Name", "Revenue", "Expenses", "Assets", "Tax_Year", "Last Updated", "EIN", "Filing_PDF"]
    
    # Safely reorder columns
    df = df.reindex(columns=cols)
    
    csv_filename = "nj_school_finances.csv"
    df.to_csv(csv_filename, index=False)
    print(f"Saved financial data to {csv_filename}")

    collect_tuition_costs(DOE_YEARS)

    public_status = check_public_data()
    with open("public_data_status.txt", "w") as f:
        f.write(f"Last Checked: {datetime.now()}\n\n")
        f.write(public_status)
    print("Checked public data status.")

if __name__ == "__main__":
    main()
