import pandas as pd

def load_lane_data(country_code):
    # Simulated static data for now
    return pd.DataFrame({
        "lane_name": ["PL05 → PL07", "BE66 → NL35", "DE80 → BE11"],
        "origin": ["PL05", "BE66", "DE80"],
        "destination": ["PL07", "NL35", "BE11"],
        "loads": [2885, 426, 258],
    })

def flip_forecast_table(df):
    df_flipped = df.set_index("Period").T  # Set "Period" as index, then transpose
    df_flipped.columns.name = None         # Remove column group name
    return df_flipped

def load_model_results(lane):
    # Simulated results
    forecast_table = pd.DataFrame({
        "Period": ["Hist 3M", "Forecast 3M", "Hist 6M", "Forecast 6M"],
        "Marketplace": [1.52, 1.57, 1.49, 1.55],
        "Dedication": [1.62, 1.67, 1.59, 1.65],
        "EST": [1.57, 1.62, 1.57, 1.62]
    })

    chart_data = pd.DataFrame({
        "period": ["Hist 3M", "Forecast 3M", "Hist 6M", "Forecast 6M"] * 3,
        "rate": [1.52, 1.57, 1.49, 1.55, 1.62, 1.67, 1.59, 1.65, 1.57, 1.62, 1.57, 1.62],
        "type": ["Marketplace"] * 4 + ["Dedication"] * 4 + ["EST"] * 4
    })

    summary = {
        "total_loads": 2885,
        "distance_km": 150.3,
        "sender_pct": 98.99,
        "est_pct": 1.01,
        "forecast_table": forecast_table
    }

    return summary, chart_data
