import pandas as pd
import os

def calculate_base_potential(df_transactions):
    """Calculates the highest historical sales month for each outlet."""
    
    # 1. Group by Year, Month, and Outlet to get total monthly volume per shop
    # (We use 'Year' and 'Month' columns because 'Date' doesn't exist in this raw CSV!)
    monthly_sales = df_transactions.groupby(['Outlet_ID', 'Year', 'Month'])['Volume_Liters'].sum().reset_index()
    
    # 2. Find the absolute maximum historical month for each outlet
    base_potential = monthly_sales.groupby('Outlet_ID')['Volume_Liters'].max().reset_index()
    
    # 3. Rename column to reflect historical max peak
    base_potential.rename(columns={'Volume_Liters': 'Historical_Max_Volume'}, inplace=True)
    
    return base_potential

if __name__ == "__main__":
    print("🚀 Loading transaction history from Bronze...")
    
    # Load the raw transactions file
    input_path = '../data/bronze/transactions_history_final.csv'
    
    if not os.path.exists(input_path):
        print(f"❌ Error: Could not find the file at {input_path}")
    else:
        df_trans = pd.read_csv(input_path)
        
        print("📊 Calculating historical max peaks per outlet...")
        df_base_potential = calculate_base_potential(df_trans)
        
        print("\n--- Base Potential Preview (Top 5 Rows) ---")
        print(df_base_potential.head())
        
        # Ensure output directory exists and save base potential
        os.makedirs("../data/silver", exist_ok=True)
        df_base_potential.to_csv("../data/silver/base_potential_baseline.csv", index=False)
        print("\n✅ Base potential calculation complete and saved to Silver layer!")