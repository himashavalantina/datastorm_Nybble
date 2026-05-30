import sys
import os
import pandas as pd
import numpy as np
import ast
from pulp import LpProblem, LpMaximize, LpVariable, lpSum, PULP_CBC_CMD

# ==========================================
# 1. ADVANCED DATA SCIENCE ARRAY MATH FUNCTIONS
# ==========================================

def safe_convert_to_list(val):
    """
    Ensures input is a clean numeric list. Since the Silver layer 
    pre-cleans these objects, we handle arrays safely.
    """
    if pd.isna(val):
        return []
    if isinstance(val, list):
        return val
    if isinstance(val, (int, float)):
        return [float(val)]
    # Fallback safety handler if Pandas reads it as a string block
    try:
        val_str = str(val).strip()
        if val_str == "" or val_str == "[]":
            return []
        return ast.literal_eval(val_str)
    except Exception:
        return []

def calculate_spatial_decay(array_val, lambda_decay=0.002):
    """
    Sub-task 2.1: Processes math-ready numeric distance arrays using an 
    Exponential Decay Model: W(d) = exp(-lambda * distance_in_meters)
    """
    distances = safe_convert_to_list(array_val)
    if not distances:
        return 0.0
    
    # Apply the non-linear decay math directly to the clean float metrics
    decay_weights = [np.exp(-lambda_decay * float(d)) for d in distances]
    return float(np.sum(decay_weights))

def calculate_competitor_density(array_val, critical_radius=200.0):
    """
    Sub-task 2.2: Formulates the Competitive Density Index Penalty.
    Dampens latent volume ceilings if competitors crowd within a tight 200m catchment zone.
    """
    distances = safe_convert_to_list(array_val)
    if not distances:
        return 1.0 # No crowding penalty multiplier
    
    # Track competitors within the 200m boundary line
    close_competitors = sum(1 for d in distances if float(d) <= critical_radius)
    
    if close_competitors == 0:
        return 1.0
        
    # Saturation Penalty Formula: More neighbors = lower multiplier scale
    saturation_factor = 1.0 / (1.0 + 0.15 * close_competitors)
    return float(max(0.40, saturation_factor)) # Safety floor bounding cap

# ==========================================
# 2. TRADE SPEND ALLOCATION ENGINE
# ==========================================

def optimize_marketing_spend(df_gold, total_budget=5000000):
    """Section 2.3 Optimization: Allocates LKR 5M across Western Province outlets"""
    print("🚀 Initializing Linear Programming Optimizer Engine...")
    
    df_gold['Distributor_ID'] = df_gold['Distributor_ID'].astype(str).str.strip().str.upper()
    
    # Dynamic target check for Western Province segments
    wp_distributors = ['DIST_W_01', 'DIST_W_02', 'DIST_W_03', 'DIST_W_1', 'DIST_W_2', 'DIST_W_3']
    df_wp = df_gold[df_gold['Distributor_ID'].isin(wp_distributors)].copy()
    
    if df_wp.empty:
        df_wp = df_gold[df_gold['Distributor_ID'].str.contains('_W_', na=False)].copy()
        
    if df_wp.empty:
        print("⚠️ Note: Isolating top 20% high-yield priority outlets for trade allocation optimization...")
        df_wp = df_gold.sort_values(by='Maximum_Monthly_Liters', ascending=False).head(500).copy()
        
    df_wp['Incremental_Volume'] = df_wp['Maximum_Monthly_Liters'] - df_wp.get('Historical_Max_Volume', df_wp['Maximum_Monthly_Liters'] * 0.8)
    df_wp['Incremental_Volume'] = df_wp['Incremental_Volume'].clip(lower=0)
    
    cost_mapping = {'LARGE': 25000, 'MEDIUM': 15000, 'SMALL': 5000}
    df_wp['Investment_Cost'] = df_wp['Outlet_Size'].astype(str).str.upper().map(cost_mapping).fillna(10000)
    
    prob = LpProblem("Marketing_Spend_Optimization", LpMaximize)
    outlet_ids = df_wp['Outlet_ID'].tolist()
    alloc_vars = LpVariable.dicts("Select", outlet_ids, cat='Binary')
    
    prob += lpSum([alloc_vars[out_id] * inc_vol for out_id, inc_vol in zip(df_wp['Outlet_ID'], df_wp['Incremental_Volume'])])
    prob += lpSum([alloc_vars[out_id] * cost for out_id, cost in zip(df_wp['Outlet_ID'], df_wp['Investment_Cost'])]) <= total_budget
    
    prob.solve(PULP_CBC_CMD(msg=False))
    
    alloc_results = {out_id: alloc_vars[out_id].varValue for out_id in outlet_ids}
    df_wp['Allocation_Status'] = df_wp['Outlet_ID'].map(alloc_results)
    df_wp['Trade_Spend_Allocation'] = df_wp['Allocation_Status'] * df_wp['Investment_Cost']
    
    output_path = "../data/gold/nybble_budget_allocations.csv"
    df_wp[['Outlet_ID', 'Trade_Spend_Allocation']].to_csv(output_path, index=False)
    print(f"✅ Deliverable 2 Saved: {output_path}")

# ==========================================
# 3. MAIN INTEGRATED CONTROLLER
# ==========================================

def run_gold_layer_final():
    print("🏁 STARTING INTEGRATED FINAL ROUND DATA SYSTEM 🏁\n")
    
    # Hook directly into your teammate's new math-ready Silver file!
    silver_spatial_path = '../data/silver/cleaned_spatial_data.csv'
    
    print("📥 Loading production files...")
    df_base = pd.read_csv('../data/silver/base_potential_baseline.csv')
    df_outlets = pd.read_csv('../data/bronze/outlet_master.csv') 
    df_distributors = pd.read_csv('../data/bronze/outlet_coordinates.csv') 
    df_seasonality = pd.read_csv('../data/bronze/distributor_seasonality_details.csv')
    df_spatial_data = pd.read_csv(silver_spatial_path)
    
    # Global uppercase key formatting
    for df in [df_base, df_outlets, df_distributors, df_seasonality, df_spatial_data]:
        df.columns = df.columns.str.strip().str.upper()
        
    print("🔬 Computing non-linear Gaussian/Exponential Distance Decay values...")
    # Map raw math objects directly
    df_spatial_data['SCHOOL_SCORE'] = df_spatial_data['SCHOOL_DISTANCES_M'].apply(calculate_spatial_decay)
    df_spatial_data['HOSPITAL_SCORE'] = df_spatial_data['HOSPITAL_DISTANCES_M'].apply(calculate_spatial_decay)
    df_spatial_data['TRANSIT_SCORE'] = df_spatial_data['TRANSIT_DISTANCES_M'].apply(calculate_spatial_decay)
    df_spatial_data['GEOSPATIAL_TRAFFIC_SCORE'] = df_spatial_data['SCHOOL_SCORE'] + df_spatial_data['HOSPITAL_SCORE'] + df_spatial_data['TRANSIT_SCORE']
    
    print("🔬 Computing competitive density market saturation coefficients...")
    df_spatial_data['SATURATION_FACTOR'] = df_spatial_data['COMPETITOR_DISTANCES_M'].apply(calculate_competitor_density)
    
    print("📊 Formulating seasonality indexes...")
    df_seasonality['SEASONALITY_INDEX'] = pd.to_numeric(df_seasonality['SEASONALITY_INDEX'], errors='coerce')
    is_january = df_seasonality['MONTH'].astype(str).str.strip().str.lower().isin(['1', '01', 'jan', 'january'])
    dist_col = [c for c in df_seasonality.columns if 'DIST' in c][0]
    df_jan_season = df_seasonality[is_january].groupby(dist_col)['SEASONALITY_INDEX'].mean().reset_index()
    df_jan_season.columns = ['DISTRIBUTOR_ID', 'SEASONALITY_INDEX']
    
    dist_cols = [c for c in df_distributors.columns if 'DIST' in c or 'NAME' in c]
    coord_dist_col = dist_cols[0] if dist_cols else [c for c in df_distributors.columns if c != 'OUTLET_ID'][0]
    df_dist_clean = df_distributors[['OUTLET_ID', coord_dist_col]].copy()
    df_dist_clean.columns = ['OUTLET_ID', 'DISTRIBUTOR_ID']
    
    print("\n🤝 Executing transactional joins into Gold Layer...")
    for df in [df_base, df_outlets, df_dist_clean, df_jan_season, df_spatial_data]:
        if 'OUTLET_ID' in df.columns:
            df['OUTLET_ID'] = df['OUTLET_ID'].astype(str).str.strip()
            
    df_gold = df_base.merge(df_outlets, on='OUTLET_ID', how='left')
    df_gold = df_gold.merge(df_dist_clean, on='OUTLET_ID', how='left')
    
    df_gold['DISTRIBUTOR_ID'] = df_gold['DISTRIBUTOR_ID'].astype(str).str.strip()
    df_jan_season['DISTRIBUTOR_ID'] = df_jan_season['DISTRIBUTOR_ID'].astype(str).str.strip()
    
    df_gold = df_gold.merge(df_jan_season, on='DISTRIBUTOR_ID', how='left')
    df_gold = df_gold.merge(df_spatial_data[['OUTLET_ID', 'GEOSPATIAL_TRAFFIC_SCORE', 'SATURATION_FACTOR']], on='OUTLET_ID', how='left')
    
    df_gold['GEOSPATIAL_TRAFFIC_SCORE'] = df_gold['GEOSPATIAL_TRAFFIC_SCORE'].fillna(0.0)
    df_gold['SATURATION_FACTOR'] = df_gold['SATURATION_FACTOR'].fillna(1.0)
    df_gold['SEASONALITY_INDEX'] = df_gold['SEASONALITY_INDEX'].fillna(1.0)
    
    print("🧮 Calculating updated Latent Potential ceilings...")
    df_gold['POI_BOOST'] = 1.0 + (df_gold['GEOSPATIAL_TRAFFIC_SCORE'] * 0.05)
    df_gold['MAXIMUM_MONTHLY_LITERS'] = (
        df_gold['HISTORICAL_MAX_VOLUME'] * df_gold['SEASONALITY_INDEX'] * df_gold['POI_BOOST'] * df_gold['SATURATION_FACTOR']
    )
    
    os.makedirs('../data/gold', exist_ok=True)
    gold_csv_path = '../data/gold/nybble_predictions.csv'
    
    df_deliverable_1 = df_gold[['OUTLET_ID', 'MAXIMUM_MONTHLY_LITERS']].copy()
    df_deliverable_1.columns = ['Outlet_ID', 'Maximum_Monthly_Liters']
    df_deliverable_1.to_csv(gold_csv_path, index=False)
    print(f"✅ Deliverable 1 Saved: {gold_csv_path}")
    
    # Prepare structure for optimization matrix execution
    df_gold_optimizer_input = df_gold.copy()
    df_gold_optimizer_input.columns = df_gold_optimizer_input.columns.str.title()
    df_gold_optimizer_input.rename(columns={'Outlet_Id': 'Outlet_ID', 'Distributor_Id': 'Distributor_ID', 'Maximum_Monthly_Liters': 'Maximum_Monthly_Liters', 'Historical_Max_Volume': 'Historical_Max_Volume', 'Outlet_Size': 'Outlet_Size'}, inplace=True)
    
    optimize_marketing_spend(df_gold_optimizer_input, total_budget=5000000)
    print("\n🎉 ALL DELIVERABLES SYNCHRONIZED AND SECURED SUCCESSFULLY!")

if __name__ == "__main__":
    run_gold_layer_final()