import pandas as pd
import os
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

if __name__ == "__main__":
    # 1. Load the data
    df_outlets = pd.read_csv('../data/bronze/outlet_master.csv')
    
    # 2. Print columns (Optional, but good for debugging)
    print("Actual columns in outlet_master.csv:", df_outlets.columns.tolist())
    
    # 3. Clean duplicates
    df_clean_outlets = check_duplicates(df_outlets, primary_keys=['Outlet_ID'], source_file='outlet_master')
    
    # 4. Clean nulls using columns that actually exist in the file
    df_clean_outlets = check_nulls(df_clean_outlets, mandatory_columns=['Outlet_ID', 'Outlet_Type'], source_file='outlet_master')
    
    # 5. Save the silver data
    df_clean_outlets.to_csv('../data/silver/cleaned_outlet_master.csv', index=False)
    print("✅ Silver layer cleaning complete for outlet_master.csv")
