import requests
import pandas as pd
from datetime import datetime
import os

# --- CONFIGURATION ---
# Add more schools here. You can find EINs on ProPublica or GuideStar.
SCHOOLS = [
    {"Name": "Princeton University", "EIN": "210634501"},
    {"Name": "Seton Hall University", "EIN": "221500645"},
    {"Name": "Stevens Institute of Technology", "EIN": "221487354"},
    {"Name": "Rider University", "EIN": "210650678"},
    {"Name": "TCNJ Foundation", "EIN": "222448189"}, # Public schools often use Foundations for non-profit status
    {"Name": "Destination College (Example)", "EIN": "222479262"} # Replace with your target non-profit
]

# NJDOE Public Data URL Pattern (Checks for current and next year)
CURRENT_YEAR = datetime.now().year
PUBLIC_DATA_URLS = [
    f"https://www.nj.gov/education/guide/{CURRENT_YEAR}/excel/indicator1.xls",
    f"https://www.nj.gov/education/guide/{CURRENT_YEAR - 1}/excel/indicator1.xls"
]

def fetch_nonprofit_data(ein):
    """
    Fetches the most recent financial filing from ProPublica's API.
    """
    url = f"https://projects.propublica.org/nonprofits/api/v2/organizations/{ein}.json"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            # Get the most recent filing (usually the first in the list)
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
    """
    Checks if the NJ Department of Education has released the new budget Excel file.
    Returns the status message.
    """
    status_messages = []
    for url in PUBLIC_DATA_URLS:
        try:
            # We only need the headers to check if it exists (HEAD request)
            response = requests.head(url, timeout=5)
            if response.status_code == 200:
                status_messages.append(f"AVAILABLE: {url}")
            else:
                status_messages.append(f"NOT RELEASED YET: {url} (Status {response.status_code})")
        except:
            status_messages.append(f"ERROR CHECKING: {url}")
    return "\n".join(status_messages)

def main():
    print("--- Starting Financial Scrape ---")
    results = []
    
    # 1. Fetch Private/Non-Profit Data
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
            row.update({"Revenue": 0, "Expenses": 0, "Assets": 0, "Tax_Year": "Error"})
            
        results.append(row)

    # 2. Save to CSV
    df = pd.DataFrame(results)
    # Reorder columns for readability
    cols = ["School Name", "Revenue", "Expenses", "Assets", "Tax_Year", "Last Updated", "EIN", "Filing_PDF"]
    df = df[cols]
    
    csv_filename = "nj_school_finances.csv"
    df.to_csv(csv_filename, index=False)
    print(f"Saved financial data to {csv_filename}")

    # 3. Check Public Data Status
    public_status = check_public_data()
    with open("public_data_status.txt", "w") as f:
        f.write(f"Last Checked: {datetime.now()}\n\n")
        f.write(public_status)
    print("Checked public data status.")

if __name__ == "__main__":
    main()
