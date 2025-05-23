import pandas as pd

def load_lane_data(country_code):
    # Simulated static data for now
    return pd.DataFrame({
        "lane_name": ["PL05 → PL07", "BE66 → NL35", "DE80 → BE11"],
        "origin": ["PL05", "BE66", "DE80"],
        "destination": ["PL07", "NL35", "BE11"],
        "loads": [2885, 426, 258],
    })


def combine_results_with_predictions(forecast_table: pd.DataFrame, actual_data_table: pd.DataFrame) -> pd.DataFrame:
    # Step 1: Format both tables so 'Period' is index and types are rows
    forecast_df = forecast_table.set_index("Period").T
    actual_df = actual_data_table.set_index("Period").T

    # Step 2: Concatenate along columns
    combined = pd.concat([forecast_df, actual_df], axis=1)

    # Optional: Rename columns for clarity
    combined.columns = ["Forecast 3M", "Forecast 6M", "Historical 3M", "Historical 6M"]

    # Reset index if needed
    combined.reset_index(inplace=True)
    combined.rename(columns={"index": "Type"}, inplace=True)
    return combined

def load_model_results(lane):

    #TODO: This would pull the data from a DB
    # It would also be pulling raw data
    # TODO: set up a mock pull of raw data & so it processes it within streamlit
    # If i can get the expected visualistions pinned down it should just involve massaging the underlying data per client

    # What is the most logical
    # Simulated results
    forecast_table = pd.DataFrame({
        "Period": ["Forecast 3M", "Forecast 6M"],
        "Marketplace": [ 1.57, 1.55],
        "Dedication": [1.67, 1.65],
        "EST": [1.62, 1.62]
    })

    actual_data_table = pd.DataFrame({
        "Period": ["Hist 3M", "Hist 6M"],
        "Marketplace": [1.55, 1.48],
        "Dedication": [1.62, 1.60],
        "EST": [1.67, 1.56]
    })

    merged_results = combine_results_with_predictions(forecast_table, actual_data_table)

    # Map actual to forecast periods
    actual_data_table["Period"] = actual_data_table["Period"].str.replace("Hist", "Forecast")

    # Merge on Period
    combined = pd.merge(forecast_table, actual_data_table, on="Period", suffixes=("_Pred", "_Actual"))

    # Melt to long format
    rows = []
    for _, row in combined.iterrows():
        for col in ["Marketplace", "Dedication", "EST"]:
            pred = row[f"{col}_Pred"]
            actual = row[f"{col}_Actual"]
            delta = pred - actual
            percent_error = (delta / actual) * 100 if actual != 0 else None
            period_name = row["Period"].removeprefix("Forecast ")

            rows.append({
                "Period": period_name,
                "Type": col,
                "Actual": round(actual, 2),
                "Predicted": round(pred, 2),
                "Delta (€/km)": round(delta, 3),
                "% Error": f"{round(percent_error, 2)}%"
            })

    chart_data = pd.DataFrame(rows)

    summary = {
        "total_loads": 2885,
        "distance_km": 150.3,
        "sender_pct": 98.99,
        "est_pct": 1.01,
        "forecast_table": merged_results
    }

    return summary, chart_data
