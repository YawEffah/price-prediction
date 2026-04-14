import pandas as pd
import os

def transform_data():
    input_file = 'scratch/wfp_food_prices_gha.csv'
    output_dir = 'static/gh_data'
    os.makedirs(output_dir, exist_ok=True)

    # SOURCE: WFP Ghana Food Prices
    # DATE RANGE: January 2006 to June 2023
    # Average monthly rainfall for Ghana (mm)
    ghana_rainfall = {
        1: 15, 2: 30, 3: 80, 4: 140, 5: 180, 6: 200,
        7: 120, 8: 80, 9: 150, 10: 150, 11: 50, 12: 20
    }

    df = pd.read_csv(input_file)
    
    # Convert date to datetime and extract Month/Year
    df['date'] = pd.to_datetime(df['date'])
    df['Month'] = df['date'].dt.month
    df['Year'] = df['date'].dt.year

    # Filter columns
    df = df[['Month', 'Year', 'commodity', 'price']]

    commodities = df['commodity'].unique()

    for commodity in commodities:
        print(f"Processing {commodity}...")
        comm_df = df[df['commodity'] == commodity].copy()
        
        # Aggregate by Month and Year
        agg_df = comm_df.groupby(['Month', 'Year']).agg({'price': 'mean'}).reset_index()
        
        # Add Rainfall column based on Month
        agg_df['Rainfall'] = agg_df['Month'].map(ghana_rainfall)
        
        # Rename price to WPI to stay compatible with the model expectance
        # We will use actual price as WPI and later set base=100
        agg_df = agg_df.rename(columns={'price': 'WPI'})
        
        # Reorder columns: Month, Year, Rainfall, WPI
        agg_df = agg_df[['Month', 'Year', 'Rainfall', 'WPI']]
        
        # Sort by Year and then Month
        agg_df = agg_df.sort_values(by=['Year', 'Month'])

        # Save to CSV
        safe_name = commodity.replace(' ', '_').replace('(', '').replace(')', '').replace(',', '').lower()
        agg_df.to_csv(f"{output_dir}/{safe_name}.csv", index=False)

if __name__ == "__main__":
    transform_data()
