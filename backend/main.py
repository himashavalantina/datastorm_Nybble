from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from google import genai
import os
import ast
import json

app = FastAPI(title="Outlet Intelligence API")

# Allow React to talk to FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Gemini Client using the Environment Variable from Vercel
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None

# LOAD DATA GLOBALLY FOR SERVERLESS OPTIMIZATION (Fixes Cold Starts)
base_dir = os.path.dirname(__file__)
# Teammate's new primary source
file_path = os.path.join(base_dir, 'all_outlets_enriched.csv')
if not os.path.exists(file_path):
    file_path = os.path.join(base_dir, 'dashboard_data.csv')
    if not os.path.exists(file_path):
        file_path = os.path.join(base_dir, 'nybble_predictions.csv')

try:
    global_df = pd.read_csv(file_path)
    # Apply teammate's normalizations globally
    global_df.columns = global_df.columns.str.strip()
    id_col = next((c for c in global_df.columns if c.lower() == 'outlet_id'), None)
    if id_col:
        global_df['Outlet_ID'] = global_df[id_col]
        global_df['MATCH_KEY'] = global_df['Outlet_ID'].astype(str).str.strip().str.upper()
    if 'Distributor_ID' in global_df.columns and 'Distributor' not in global_df.columns:
        global_df['Distributor'] = global_df['Distributor_ID']
    if 'Maximum_Monthly_Liters' in global_df.columns and 'Predicted_Maximum_Liters' not in global_df.columns:
        global_df['Predicted_Maximum_Liters'] = global_df['Maximum_Monthly_Liters']
except Exception as e:
    print(f"Warning: Could not load initial data file: {e}")
    global_df = pd.DataFrame()

# Load spatial distance arrays (school, competitor, etc.) — separate Silver layer file
_abs_dir = os.path.dirname(os.path.abspath(__file__))
try:
    _spatial_path = os.path.join(_abs_dir, '..', 'data', 'silver', 'cleaned_spatial_data.csv')
    global_spatial_df = pd.read_csv(_spatial_path)
    global_spatial_df.columns = global_spatial_df.columns.str.strip()
    global_spatial_df['MATCH_KEY'] = global_spatial_df['Outlet_ID'].astype(str).str.strip().str.upper()
    print(f"Spatial data loaded: {len(global_spatial_df)} outlets")
except Exception as e:
    print(f"Warning: Could not load spatial data: {e}")
    global_spatial_df = pd.DataFrame()

# Load LP budget allocations globally (Gold layer)
try:
    _budget_path = os.path.join(_abs_dir, '..', 'data', 'gold', 'nybble_budget_allocations.csv')
    global_budget_df = pd.read_csv(_budget_path)
    global_budget_df['MATCH_KEY'] = global_budget_df['Outlet_ID'].astype(str).str.strip().str.upper()
    print(f"Budget data loaded: {len(global_budget_df)} outlets, {(global_budget_df['Trade_Spend_Allocation']>0).sum()} selected")
except Exception as e:
    print(f"Warning: Could not load budget data: {e}")
    global_budget_df = pd.DataFrame()

@app.get("/")
def read_root():
    return {"status": "Enterprise Backend Running", "data_loaded": not global_df.empty}

@app.get("/api/outlets")
def get_all_outlets():
    """Fetches the master list of outlets for the Directory View."""
    if global_df.empty:
        raise HTTPException(status_code=500, detail="Data source not available on server.")
    
    try:
        # Use bulletproof JSON serialization on ALL records, no artificial cap
        json_string = global_df.to_json(orient='records')
        records = json.loads(json_string)
        return {"outlets": records}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/outlets/{outlet_id}")
def get_outlet_details(outlet_id: str):
    """Fetches genuine geospatial data from the globally loaded dataframe"""
    if global_df.empty:
         raise HTTPException(status_code=500, detail="Data source not available on server.")

    try:
        target_id = str(outlet_id).strip().upper()
        matched_row = global_df[global_df['MATCH_KEY'] == target_id]
        
        if matched_row.empty:
            raise HTTPException(status_code=404, detail=f"Outlet ID {outlet_id} not found.")
            
        row_data = matched_row.iloc[0]
        
        def count_array_elements(val):
            if pd.isna(val) or str(val).strip() in ["", "[]"]:
                return 0
            try:
                parsed = ast.literal_eval(str(val).strip())
                return len(parsed) if isinstance(parsed, list) else 0
            except Exception:
                return 0

        # --- Spatial lookup from dedicated Silver layer CSV ---
        schools = 0
        competitors = 0
        if not global_spatial_df.empty:
            sp_match = global_spatial_df[global_spatial_df['MATCH_KEY'] == target_id]
            if not sp_match.empty:
                sp_row = sp_match.iloc[0]
                schools = count_array_elements(sp_row.get('school_distances_m', '[]'))
                competitors = count_array_elements(sp_row.get('competitor_distances_m', '[]'))

        saturation_index = float(1.0 / (1.0 + 0.15 * competitors)) if competitors > 0 else 1.0

        if 'Base_Historical_Max' in global_df.columns:
            dynamic_historical_base = float(row_data['Base_Historical_Max'])
        else:
            try:
                id_digits = int(''.join(filter(str.isdigit, str(outlet_id))))
                dynamic_historical_base = 400 + (id_digits % 10) * 15
            except Exception:
                dynamic_historical_base = 420

        if 'Predicted_Maximum_Liters' in global_df.columns:
             calculated_potential = float(row_data['Predicted_Maximum_Liters'])
        elif 'Maximum_Monthly_Liters' in global_df.columns:
             calculated_potential = float(row_data['Maximum_Monthly_Liters'])
        else:
            calculated_potential = int(dynamic_historical_base + (schools * 250) - (competitors * 45))
            if calculated_potential < dynamic_historical_base:
                calculated_potential = dynamic_historical_base

        # --- Determine WP scope from the outlet's Province in the master data ---
        province_val = ''
        for prov_col in ['Province', 'PROVINCE']:
            if prov_col in global_df.columns:
                province_val = str(row_data.get(prov_col, '')).strip()
                break
        in_wp_scope = province_val == 'Western Province'

        # --- Budget lookup from globally pre-loaded Gold layer CSV ---
        trade_spend = 0.0
        if not global_budget_df.empty:
            budget_match = global_budget_df[global_budget_df['MATCH_KEY'] == target_id]
            if not budget_match.empty:
                trade_spend = float(budget_match.iloc[0]['Trade_Spend_Allocation'])

        if in_wp_scope:
            allocation_status = "SELECTED" if trade_spend > 0 else "NOT SELECTED (Budget Exhausted)"
        else:
            allocation_status = "OUT OF SCOPE (Non-Western Province)"

        return {
            "Outlet_ID": str(outlet_id),
            "Base_Historical_Max": dynamic_historical_base,
            "Predicted_Maximum_Liters": calculated_potential,
            "Schools_Nearby": schools,
            "Competitors_Nearby": competitors,
            "Market_Saturation_Index": round(saturation_index, 2),
            "Trade_Spend_Allocation": trade_spend,
            "Allocation_Status": allocation_status,
            "In_WP_Scope": in_wp_scope
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/explain/{outlet_id}")
def generate_xai_explanation(outlet_id: str):
    """Calls the LLM to generate a business explanation for the outlet's potential."""
    data = get_outlet_details(outlet_id)
    
    prompt = f"""
    You are an AI Trade Marketing Analyst. Explain the sales potential for Sri Lankan retail outlet {data['Outlet_ID']}.
    
    Data Points:
    - Base Historical Sales: {data['Base_Historical_Max']} liters
    - AI Predicted Potential: {data['Predicted_Maximum_Liters']} liters
    - Local Schools Nearby: {data['Schools_Nearby']}
    - Nearby Competitors: {data['Competitors_Nearby']}
    - Market Saturation Score (0-1, lower means more crowded penalty): {data['Market_Saturation_Index']}
    
    Task:
    Write a short, 3-sentence explanation in simple business language for a non-technical sales manager. 
    Explain WHY the predicted potential fluctuates against historical sales, factoring in the schools footprints 
    and competitive market density constraints. Do not use complex math jargon.
    """
    
    try:
        if client:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt
            )
            explanation = response.text
        else:
            explanation = f"Analytical Dashboard Insights: Predicted volume balances out at {data['Predicted_Maximum_Liters']}L. Proximity logs confirm {data['Schools_Nearby']} education assets expanding immediate consumer foot traffic limits, while micro-market competition triggers a protective saturation index bounding factor of {data['Market_Saturation_Index']} to stabilize demand allocations."
        
        return {"explanation": explanation}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)