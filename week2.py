# Week 2 Deliverable: EDA and Dataset Validation
# Inputs:  CRMLSSold.csv, CRMLSListing.csv (already filtered to Residential from Week 1)
# Outputs: sold_clean.csv, listing_clean.csv
 
import pandas as pd
import numpy as np

# Load data
 
sold = pd.read_csv("sold.csv", low_memory=False)
listing = pd.read_csv("listings.csv", low_memory=False)
 
# Drop duplicate .1 columns from listing (artifact of duplicate field names in extraction script)
dup_cols = [col for col in listing.columns if col.endswith(".1")]
listing.drop(columns=dup_cols, inplace=True)
 

 
print("=" * 60)
print("SOLD – STRUCTURE")
print("=" * 60)
print(f"Rows:    {sold.shape[0]:,}")
print(f"Columns: {sold.shape[1]}")
print("\nColumn data types:")
print(sold.dtypes.to_string())
 
print("\n")
print("=" * 60)
print("LISTING – STRUCTURE")
print("=" * 60)
print(f"Rows:    {listing.shape[0]:,}")
print(f"Columns: {listing.shape[1]}")
print("\nColumn data types:")
print(listing.dtypes.to_string())
 
# Unique property types

print("\n")
print("=" * 60)
print("SOLD – UNIQUE PROPERTY TYPES")
print("=" * 60)
sold_types = sold["PropertyType"].value_counts(dropna=False)
print(sold_types.to_string())
 
print("\n")
print("=" * 60)
print("LISTING – UNIQUE PROPERTY TYPES")
print("=" * 60)
listing_types = listing["PropertyType"].value_counts(dropna=False)
print(listing_types.to_string())
 

# STEP 3: FILTERING LOGIC (already Residential from Week 1,
# but re-confirming and re-applying here for documentation)
#
 
print("\n")
print("=" * 60)
print("FILTERING LOGIC APPLIED")
print("=" * 60)
 
print("\nSOLD:")
print(f"  Rows before Residential filter: {sold.shape[0]:,}")
sold = sold[sold["PropertyType"] == "Residential"]
print(f"  Rows after Residential filter:  {sold.shape[0]:,}")
 
print("\nLISTING:")
print(f"  Rows before Residential filter: {listing.shape[0]:,}")
listing = listing[listing["PropertyType"] == "Residential"]
print(f"  Rows after Residential filter:  {listing.shape[0]:,}")
 

# STEP 4: NULL COUNT SUMMARY + 90% MISSING FLAG

 
def null_summary(df, name):
    print("\n")
    print("=" * 60)
    print(f"{name.upper()} – NULL COUNT SUMMARY")
    print("=" * 60)
    total = len(df)
    missing = df.isnull().sum()
    pct = (missing / total * 100).round(2)
    summary = pd.DataFrame({"missing_count": missing, "missing_pct": pct})
    summary = summary.sort_values("missing_pct", ascending=False)
 
    print(f"\n{'Column':<45} {'Missing Count':>14} {'Missing %':>10}  {'Flag'}")
    print("-" * 85)
    for col, row in summary.iterrows():
        flag = "*** >90% NULL – CONSIDER DROPPING ***" if row["missing_pct"] > 90 else ""
        print(f"{col:<45} {int(row['missing_count']):>14,} {row['missing_pct']:>9.1f}%  {flag}")
 
    high_missing = summary[summary["missing_pct"] > 90].index.tolist()
    print(f"\nColumns above 90% missing: {len(high_missing)}")
    for col in high_missing:
        print(f"  {col}")
 
null_summary(sold, "Sold")
null_summary(listing, "Listing")
 

# STEP 5: NUMERIC DISTRIBUTION SUMMARY
# Fields: ClosePrice, LivingArea, DaysOnMarket

 
def numeric_distribution(df, name):
    print("\n")
    print("=" * 60)
    print(f"{name.upper()} – NUMERIC DISTRIBUTION SUMMARY")
    print("=" * 60)
 
    fields = ["ClosePrice", "LivingArea", "DaysOnMarket"]
    percentiles = [0.01, 0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95, 0.99]
 
    for field in fields:
        if field not in df.columns:
            print(f"\n{field}: column not found in {name}")
            continue
 
        series = pd.to_numeric(df[field], errors="coerce").dropna()
        print(f"\n{field}  (n={len(series):,} non-null values)")
        print(f"  Min:     {series.min():,.2f}")
        print(f"  Max:     {series.max():,.2f}")
        print(f"  Mean:    {series.mean():,.2f}")
        print(f"  Median:  {series.median():,.2f}")
        print(f"  Std Dev: {series.std():,.2f}")
        print("  Percentiles:")
        for p in percentiles:
            print(f"    p{int(p*100):>2}: {series.quantile(p):,.2f}")
 
        # Outlier count using IQR method
        q1, q3 = series.quantile(0.25), series.quantile(0.75)
        iqr = q3 - q1
        outliers = series[(series < q1 - 1.5 * iqr) | (series > q3 + 1.5 * iqr)]
        print(f"  Outliers (IQR method): {len(outliers):,} ({len(outliers)/len(series)*100:.1f}%)")
 
numeric_distribution(sold, "Sold")
numeric_distribution(listing, "Listing")
 

# STEP 6: SAVE FILTERED DATASETS

 
sold.to_csv("soldcsv", index=False)
listing.to_csv("listing.csv", index=False)
 
print("\n")
print("=" * 60)
print("OUTPUT FILES SAVED")
print("=" * 60)
print(f"sold_clean.csv    – {sold.shape[0]:,} rows, {sold.shape[1]} columns")
print(f"listing_clean.csv – {listing.shape[0]:,} rows, {listing.shape[1]} columns")
 