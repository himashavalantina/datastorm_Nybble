import pandas as pd
import os
import ast
from datetime import datetime

def quarantine_records(df_rejected, reason, source_file):
    """Saves rejected records to the quarantine store with a failure reason."""
    if df_rejected.empty:
        return
    
    # Ensure the rejected directory exists
    quarantine_dir = "../data/silver/rejected"
    os.makedirs(quarantine_dir, exist_ok=True)
    
    # Add audit columns
    df_rejected = df_rejected.copy()
    df_rejected['failure_reason'] = reason
    df_rejected['quarantine_timestamp'] = datetime.now().isoformat()
    
    # Save to CSV
    filename = f"rejected_{source_file}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    filepath = os.path.join(quarantine_dir, filename)
    df_rejected.to_csv(filepath, index=False)
    print(f"⚠️ Quarantined {len(df_rejected)} records from {source_file} due to: {reason}")

def check_nulls(df, mandatory_columns, source_file):
    """Filters out rows with nulls in mandatory columns and quarantines them."""
    null_mask = df[mandatory_columns].isnull().any(axis=1)
    
    df_rejected = df[null_mask]
    df_clean = df[~null_mask]
    
    quarantine_records(df_rejected, f"Null values found in mandatory columns", source_file)
        
    return df_clean

def check_duplicates(df, primary_keys, source_file):
    """Filters out duplicate rows based on primary keys and quarantines them."""
    # Keep the first occurrence as clean, quarantine the duplicates
    dup_mask = df.duplicated(subset=primary_keys, keep='first')
    
    df_rejected = df[dup_mask]
    df_clean = df[~dup_mask]
    
    quarantine_records(df_rejected, f"Duplicate rows detected based on {primary_keys}", source_file)
        
    return df_clean

def parse_spatial_arrays(df, array_columns, source_file):
    """Safely parses stringified arrays back into Python lists and quarantines malformed rows."""
    df_clean = df.copy()
    
    for col in array_columns:
        # Custom function to safely evaluate the string, returning "ERROR" if it fails
        def safe_eval(val):
            try:
                # ast.literal_eval safely turns "[1, 2]" into the Python list [1, 2]
                return ast.literal_eval(val) if isinstance(val, str) else val
            except (ValueError, SyntaxError):
                return "ERROR"
        
        df_clean[col] = df_clean[col].apply(safe_eval)
        
        # Identify any rows where the API returned corrupted/un-parsable JSON
        error_mask = df_clean[col] == "ERROR"
        if error_mask.any():
            df_rejected = df_clean[error_mask].copy()
            df_clean = df_clean[~error_mask] # Remove bad rows
            quarantine_records(df_rejected, f"Malformed spatial array in {col}", source_file)
            
    return df_clean

def check_format_type(df, column, prefix, source_file):
    """Validates that a field conforms to an expected string format (e.g., starts with a prefix)."""
    # Mask for rows that DO NOT start with the expected prefix
    invalid_mask = ~df[column].astype(str).str.startswith(prefix)
    
    df_rejected = df[invalid_mask]
    df_clean = df[~invalid_mask]
    
    quarantine_records(df_rejected, f"Format check failed: {column} must start with '{prefix}'", source_file)
        
    return df_clean

if __name__ == "__main__":
    # --- 1. Clean Original Master Data ---
    df_outlets = pd.read_csv('../data/bronze/outlet_master.csv')
    df_clean_outlets = check_duplicates(df_outlets, primary_keys=['Outlet_ID'], source_file='outlet_master')
    df_clean_outlets = check_nulls(df_clean_outlets, mandatory_columns=['Outlet_ID', 'Outlet_Type'], source_file='outlet_master')
    df_clean_outlets.to_csv('../data/silver/cleaned_outlet_master.csv', index=False)
    print("✅ Silver layer cleaning complete for outlet_master.csv")
    
    # --- 2. Clean New Spatial Data ---
    print("\nProcessing Spatial Data (Silver Layer)...")
    spatial_file = '../data/bronze/external/scraped_spatial_arrays_backup.csv'
    
    if os.path.exists(spatial_file):
        df_spatial = pd.read_csv(spatial_file)
        
        # A. Verify Outlet_IDs are formatted correctly
        df_spatial = check_format_type(df_spatial, column='Outlet_ID', prefix='OUT_', source_file='scraped_spatial')
        
        # B. Parse the text strings back into usable Python arrays
        array_cols = ['school_distances_m', 'hospital_distances_m', 'transit_distances_m', 'competitor_distances_m']
        df_spatial = parse_spatial_arrays(df_spatial, array_columns=array_cols, source_file='scraped_spatial')
        
        # C. Save the fully cleaned, math-ready data
        df_spatial.to_csv('../data/silver/cleaned_spatial_data.csv', index=False)
        print("✅ Silver layer parsing and cleaning complete for spatial data!")
    else:
        print("⏳ Waiting for spatial backup file to be generated...")