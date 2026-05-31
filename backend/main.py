from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from google import genai
import os

app = FastAPI(title="Outlet Intelligence API")

# Allow React to talk to FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for local dev
    allow_methods=["*"],
    allow_headers=["*"],
)

# TODO: Add your Gemini API Key here (or use env variables)
# client = genai.Client(api_key="YOUR_GEMINI_API_KEY")

@app.get("/")
def read_root():
    return {"status": "Enterprise Backend Running"}

@app.get("/api/outlets")
def get_all_outlets():
    """Fetches the master list of outlets for the Directory View."""
    try:
        # Fallback to the prediction file if dashboard_data isn't generated yet
        file_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'gold', 'dashboard_data.csv')
        if not os.path.exists(file_path):
            file_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'gold', 'nybble_predictions.csv')
            
        df = pd.read_csv(file_path)
        
        # Safety net: If these columns were dropped, mock them so the UI filter requirement works
        if 'Province' not in df.columns:
            df['Province'] = 'Western Province'
        if 'Distributor' not in df.columns:
            # Assign fake distributors based on index for the demo
            df['Distributor'] = [f"Distributor_{str(i%5 + 1).zfill(2)}" for i in range(len(df))]
            
        # Limit to top 1000 to keep the React frontend lightning fast during the live demo
        records = df.head(1000).fillna("Unknown").to_dict(orient='records')
        return {"outlets": records}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/outlets/{outlet_id}")
def get_outlet_details(outlet_id: str):
    """Fetches details for a specific outlet (Mocked for now until Gold Layer is ready)"""
    mock_data = {
        "Outlet_ID": outlet_id,
        "Base_Historical_Max": 450,
        "Predicted_Maximum_Liters": 610,
        "Schools_Nearby": 2,
        "Competitors_Nearby": 5,
        "Market_Saturation_Index": 0.85
    }
    return mock_data

@app.post("/api/explain/{outlet_id}")
def generate_xai_explanation(outlet_id: str):
    """Calls the LLM to generate a business explanation for the outlet's potential."""
    
    data = get_outlet_details(outlet_id)
    
    prompt = f"""
    You are an AI Trade Marketing Analyst. Explain the sales potential for outlet {data['Outlet_ID']}.
    
    Data Points:
    - Base Historical Sales: {data['Base_Historical_Max']} liters
    - AI Predicted Potential: {data['Predicted_Maximum_Liters']} liters
    - Local Schools: {data['Schools_Nearby']}
    - Nearby Competitors: {data['Competitors_Nearby']}
    - Market Saturation Score (0-1, higher is more crowded): {data['Market_Saturation_Index']}
    
    Task:
    Write a short, 3-sentence explanation in simple business language for a non-technical sales manager. 
    Explain WHY the predicted potential is higher than historical sales, factoring in the local infrastructure 
    and the competitive crowding. Do not use complex math jargon.
    """
    
    try:
        # NOTE: Uncomment this when you add your API key!
        # response = client.models.generate_content(
        #     model='gemini-2.5-flash',
        #     contents=prompt
        # )
        # explanation = response.text
        
        # Placeholder for testing the UI
        explanation = f"Mocked AI Response: The predicted volume of {data['Predicted_Maximum_Liters']}L is higher than historical averages due to foot traffic from {data['Schools_Nearby']} nearby schools. However, the heavy local competition ({data['Market_Saturation_Index']} saturation) caps this growth, requiring targeted promotional discounts to capture market share."
        
        return {"explanation": explanation}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)