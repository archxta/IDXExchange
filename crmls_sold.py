import csv
import os
import requests
from datetime import datetime, date
 
# ============================================================
# CONFIG
# ============================================================
 
FIELDNAMES = ['BuyerAgentAOR', 'ListAgentAOR', 'Flooring', 'ViewYN', 'WaterfrontYN', 'BasementYN',
              'PoolPrivateYN', 'OriginalListPrice', 'ListingKey', 'CloseDate', 'ClosePrice',
              'ListAgentFirstName', 'ListAgentLastName', 'Latitude', 'Longitude', 'UnparsedAddress',
              'PropertyType', 'LivingArea', 'ListPrice', 'DaysOnMarket', 'ListOfficeName',
              'BuyerOfficeName', 'CoListOfficeName', 'ListAgentFullName', 'CoListAgentFirstName',
              'CoListAgentLastName', 'BuyerAgentMlsId', 'BuyerAgentFirstName', 'BuyerAgentLastName',
              'FireplacesTotal', 'AssociationFeeFrequency', 'AboveGradeFinishedArea',
              'ListingKeyNumeric', 'MLSAreaMajor', 'TaxAnnualAmount', 'CountyOrParish', 'MlsStatus',
              'ElementarySchool', 'AttachedGarageYN', 'ParkingTotal', 'BuilderName', 'PropertySubType',
              'LotSizeAcres', 'SubdivisionName', 'BuyerOfficeAOR', 'YearBuilt', 'StreetNumberNumeric',
              'ListingId', 'BathroomsTotalInteger', 'City', 'TaxYear', 'BuildingAreaTotal',
              'BedroomsTotal', 'ContractStatusChangeDate', 'ElementarySchoolDistrict',
              'CoBuyerAgentFirstName', 'PurchaseContractDate', 'ListingContractDate',
              'BelowGradeFinishedArea', 'BusinessType', 'StateOrProvince', 'CoveredSpaces',
              'MiddleOrJuniorSchool', 'FireplaceYN', 'Stories', 'HighSchool', 'Levels',
              'LotSizeDimensions', 'LotSizeArea', 'MainLevelBedrooms', 'NewConstructionYN',
              'GarageSpaces', 'HighSchoolDistrict', 'PostalCode', 'AssociationFee',
              'LotSizeSquareFeet', 'MiddleOrJuniorSchoolDistrict', 'OriginatingSystemName',
              'OriginatingSystemSubName']
 
SELECT_FIELDS = ','.join(FIELDNAMES)
 
DATA_DIR = os.path.dirname(os.path.abspath(__file__))
MASTER_PATH = os.path.join(DATA_DIR, 'sold.csv')
 
PROPERTY_API_URL = 'https://api-trestle.corelogic.com/trestle/odata/Property'
AUTH_ENDPOINT = 'https://idxexchange.com/internal-api/trestle_token.php?key=IDXEXCHANGE2026_CHANGE_THIS'
 
 
# ============================================================
# Determine which month to pull: the most recently completed
# calendar month (e.g. if today is June 2026, this pulls May 2026)
# ============================================================
today = date.today()
if today.month == 1:
    pull_year, pull_month = today.year - 1, 12
else:
    pull_year, pull_month = today.year, today.month - 1
 
month_start = datetime(pull_year, pull_month, 1)
if pull_month == 12:
    month_end = datetime(pull_year + 1, 1, 1)
else:
    month_end = datetime(pull_year, pull_month + 1, 1)
 
yyyymm = f"{pull_year}{pull_month:02d}"
monthly_csv_file = os.path.join(DATA_DIR, f"CRMLSSold{yyyymm}.csv")
 
 
# ============================================================
# STEP 1: Pull this month's closed listings from the Trestle API
# (same auth + pagination logic as the original script)
# ============================================================
 
def fetch_month_from_api():
    response = requests.get(AUTH_ENDPOINT, timeout=30)
    response.raise_for_status()
    token = response.json().get('access_token')
 
    if not token:
        print("Error retrieving token: access_token not found")
        return None
 
    headers = {'Authorization': f'Bearer {token}'}
    params = {
        '$select': SELECT_FIELDS,
        '$filter': (
            f"MlsStatus eq 'Closed' and "
            f"CloseDate ge {month_start.isoformat(timespec='milliseconds')}Z "
            f"and CloseDate lt {month_end.isoformat(timespec='milliseconds')}Z"
        ),
        '$top': 1000
    }
 
    url = PROPERTY_API_URL
    total_records = 0
 
    with open(monthly_csv_file, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=FIELDNAMES)
        writer.writeheader()
 
        while True:
            response = requests.get(url, params=params, headers=headers)
            if response.status_code != 200:
                print(f"Error: {response.status_code}")
                print(f"Error Message: {response.text}")
                break
 
            data = response.json()
            observations = data.get('value', [])
            for observation in observations:
                writer.writerow({field: observation.get(field, '') for field in FIELDNAMES})
                total_records += 1
 
            if '@odata.nextLink' in data:
                url = data['@odata.nextLink']
                params = None  # nextLink already contains the query string
            else:
                break
 
    print(f"Total {total_records} records exported to {monthly_csv_file}")
    return monthly_csv_file
 
 
# ============================================================
# STEP 2: Fold this month's data into the master sold.csv,
# filtered to PropertyType == 'Residential', without duplicating
# a month that's already been added in a previous run
# ============================================================
 
def update_master_csv(month_file):
    if month_file is None or not os.path.exists(month_file):
        print("No monthly file to merge into sold.csv — skipping update.")
        return
 
    # Read existing master and figure out which months are already in it
    if os.path.exists(MASTER_PATH):
        with open(MASTER_PATH, newline='') as f:
            reader = csv.DictReader(f)
            master_rows = list(reader)
            master_fieldnames = reader.fieldnames
        rows_before = len(master_rows)
        existing_months = {row.get('SourceMonth', '') for row in master_rows}
        print(f"Loaded existing sold.csv with {rows_before} rows.")
    else:
        master_rows = []
        master_fieldnames = FIELDNAMES + ['SourceMonth']
        rows_before = 0
        existing_months = set()
        print("No existing sold.csv found — starting fresh.")
 
    if yyyymm in existing_months:
        print(f"Month {yyyymm} is already present in sold.csv — skipping merge "
              f"to avoid duplicates.")
        return
 
    # Read this month's raw pull and filter to Residential
    with open(month_file, newline='') as f:
        reader = csv.DictReader(f)
        month_rows = list(reader)
    rows_raw = len(month_rows)
 
    filtered_rows = [row for row in month_rows if row.get('PropertyType') == 'Residential']
    rows_filtered = len(filtered_rows)
    for row in filtered_rows:
        row['SourceMonth'] = yyyymm
 
    print(f"[{yyyymm}] Read {rows_raw} rows, {rows_filtered} rows after Residential filter.")
 
    updated_rows = master_rows + filtered_rows
    rows_after = len(updated_rows)
 
    print(f"sold.csv rows BEFORE this update: {rows_before}")
    print(f"sold.csv rows AFTER this update: {rows_after}")
    assert rows_after == rows_before + rows_filtered, "Row count mismatch after merge!"
 
    with open(MASTER_PATH, mode='w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=master_fieldnames)
        writer.writeheader()
        writer.writerows(updated_rows)
 
    print(f"Saved updated sold.csv to: {MASTER_PATH}")
 
 
if __name__ == "__main__":
    month_file = fetch_month_from_api()
    update_master_csv(month_file)
 