"""
combine_crmls.py
 
Concatenates monthly CRMLSListing and CRMLSSold CSV files (January 2024 through
the most recently completed calendar month) into two combined datasets, filters
both to PropertyType == 'Residential', and saves the results as new CSVs.
 
Assumes this script lives in the same folder as the monthly CSV files
(e.g. CRMLSListing202401.csv, CRMLSSold202401.csv, etc.).
 
Note: for months where both a plain file and a "_filled" file exist
(e.g. CRMLSSold202401.csv and CRMLSSold202401_filled.csv), the "_filled"
version is used preferentially, since it is assumed to be the more complete /
corrected version. Adjust PREFER_FILLED below if that assumption is wrong.
"""
 
import re
import glob
import os
from datetime import date
import pandas as pd
 
PREFER_FILLED = True
 
# Folder containing this script and the CSVs
DATA_DIR = os.path.dirname(os.path.abspath(__file__))
 
START_YEAR_MONTH = (2024, 1)  # January 2024
 
# Most recently *completed* calendar month relative to today
today = date.today()
if today.month == 1:
    last_completed_year, last_completed_month = today.year - 1, 12
else:
    last_completed_year, last_completed_month = today.year, today.month - 1
END_YEAR_MONTH = (last_completed_year, last_completed_month)
 
 
def build_month_range(start_ym, end_ym):
    """Return list of (year, month) tuples from start to end, inclusive."""
    months = []
    y, m = start_ym
    while (y, m) <= end_ym:
        months.append((y, m))
        if m == 12:
            y, m = y + 1, 1
        else:
            m += 1
    return months
 
 
def find_file_for_month(prefix, year, month):
    """
    Find the CSV file for a given prefix (e.g. 'CRMLSListing') and year/month.
    Prefers the '_filled' variant if PREFER_FILLED is True and it exists.
    Returns the filepath, or None if no file is found for that month.
    """
    yyyymm = f"{year}{month:02d}"
    plain_path = os.path.join(DATA_DIR, f"{prefix}{yyyymm}.csv")
    filled_path = os.path.join(DATA_DIR, f"{prefix}{yyyymm}_filled.csv")
 
    if PREFER_FILLED and os.path.exists(filled_path):
        return filled_path
    if os.path.exists(plain_path):
        return plain_path
    if os.path.exists(filled_path):
        return filled_path
    return None
 
 
def combine_and_filter(prefix, months, label):
    """
    Reads, concatenates, and filters monthly CSVs for a given prefix.
    Prints row counts at each stage. Returns the filtered combined DataFrame.
    """
    frames = []
    missing_months = []
 
    for (year, month) in months:
        filepath = find_file_for_month(prefix, year, month)
        if filepath is None:
            missing_months.append(f"{year}{month:02d}")
            continue
        df = pd.read_csv(filepath, low_memory=False)
        frames.append(df)
 
    if missing_months:
        print(f"[{label}] WARNING: no file found for months: {', '.join(missing_months)}")
 
    # Row counts before concatenation (per-file counts, summed)
    rows_before_concat = sum(len(df) for df in frames)
    print(f"[{label}] Total rows across all monthly files BEFORE concatenation: {rows_before_concat}")
 
    # Concatenate all monthly frames into a single DataFrame
    combined = pd.concat(frames, ignore_index=True)
 
    # Row count after concatenation (should match rows_before_concat;
    # confirms no rows were silently dropped/added during concat)
    rows_after_concat = len(combined)
    print(f"[{label}] Total rows AFTER concatenation: {rows_after_concat}")
    assert rows_before_concat == rows_after_concat, (
        f"[{label}] Row count mismatch after concatenation! "
        f"before={rows_before_concat}, after={rows_after_concat}"
    )
 
    # Row count before Residential filter (same as rows_after_concat,
    # logged separately for clarity per the assignment instructions)
    rows_before_filter = len(combined)
    print(f"[{label}] Rows BEFORE Residential filter: {rows_before_filter}")
 
    # Filter to PropertyType == 'Residential' only
    filtered = combined[combined["PropertyType"] == "Residential"].reset_index(drop=True)
 
    # Row count after Residential filter
    rows_after_filter = len(filtered)
    print(f"[{label}] Rows AFTER Residential filter: {rows_after_filter}")
 
    return filtered
 
 
def main():
    months = build_month_range(START_YEAR_MONTH, END_YEAR_MONTH)
    print(f"Combining months {months[0][0]}-{months[0][1]:02d} "
          f"through {months[-1][0]}-{months[-1][1]:02d}\n")
 
    print("=== Processing Listings ===")
    listings_filtered = combine_and_filter("CRMLSListing", months, "Listings")
    listings_out_path = os.path.join(DATA_DIR, "listings.csv")
    listings_filtered.to_csv(listings_out_path, index=False)
    print(f"Saved combined Residential listings to: {listings_out_path}\n")
 
    print("=== Processing Sold ===")
    sold_filtered = combine_and_filter("CRMLSSold", months, "Sold")
    sold_out_path = os.path.join(DATA_DIR, "sold.csv")
    sold_filtered.to_csv(sold_out_path, index=False)
    print(f"Saved combined Residential sold records to: {sold_out_path}")
 
 
if __name__ == "__main__":
    main()