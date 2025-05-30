import streamlit as st
import pandas as pd

from data_loader import DataLoader, FilterType
import plotly.express as px
from datetime import datetime, timedelta

# --- Streamlit Setup ---
st.set_page_config(page_title="Logistics ML Dashboard", layout="wide")
st.title("🚞 Logistics Forecast Dashboard")

# --- Initialize Data Loader ---
loader = DataLoader(source="csv", path="data/fake_data.csv")

# --- URL query parameters for filter reset ---
#query_params = st.experimental_get_query_params()

# --- Reset Filters Button ---
if st.sidebar.button("🔄 Reset Filters"):
    #st.experimental_set_query_params()
    st.rerun()

# --- Dynamic Filtering ---
filters = {}

contract_options = loader.get_unique_values("contract_type")
selected_contract = st.sidebar.selectbox("Contract Type", ["All"] + contract_options)
if selected_contract != "All":
    filters["contract_type"] = selected_contract

# Step 1: Vehicle Type
vehicle_options = loader.get_unique_values("vehicle_type")
selected_vehicle = st.sidebar.selectbox("Vehicle Type", ["All"] + vehicle_options)
if selected_vehicle != "All":
    filters["vehicle_type"] = selected_vehicle

# Step 2: Pickup Postcode prefix (dependent on carrier type)
pickup_options = loader.get_unique_prefixes("origin_location_code", filters)
selected_pickup = st.sidebar.selectbox("Pickup Postcode", ["All"] + pickup_options)
if selected_pickup != "All":
    filters["origin_location_code"] = selected_pickup  + "%" # Match the prefix in the whole postcode

# Step 3: Delivery Postcode prefix (dependent on above filters)
delivery_options = loader.get_unique_prefixes("destination_location_code", filters)
selected_delivery = st.sidebar.selectbox("Delivery Postcode", ["All"] + delivery_options)
if selected_delivery != "All":
    filters["destination_location_code"] = selected_delivery + "%" # Match the prefix in the whole postcode


# Step 4: Load filtered data
@st.cache_data
def load_filtered_data(filters):
    required_columns = [
        "contract_type",
        "origin_location_code",
        "destination_location_code",
        "vehicle_type",
        "weight_kg",
        "pickup_date",
        "cost",
        "carrier_name",
        "shipper_name"
    ]
    return loader.load_filtered_data(filters, required_columns)

df = load_filtered_data(filters)

# --- Add extra fields ---
if not df.empty:
    df["pickup_date"] = pd.to_datetime(df["pickup_date"], errors='coerce')

    # Weight filter
    min_weight, max_weight = int(df["weight_kg"].min()), int(df["weight_kg"].max())
    if min_weight == max_weight:
        max_weight = min_weight + 1  # Ensure the slider has a range
    weight_range = st.sidebar.slider("Weight Range (kg)", min_value=min_weight, max_value=max_weight, value=(min_weight, max_weight))
    df = df[(df["weight_kg"] >= weight_range[0]) & (df["weight_kg"] <= weight_range[1])]

# --- Display Filtered Data ---
if not df.empty:
    # --- Summary Table for Last 3 and 12 Months ---
    st.subheader("📊 Price Summary for Last 3 and 12 Months")
    now = datetime.now()
    last_3m = df[df["pickup_date"] >= now - timedelta(days=90)]
    last_12m = df[df["pickup_date"] >= now - timedelta(days=365)]

    # --- Display DataFrame of results ---
    # st.write(df)

    def summary_stats(data, label):
        return pd.DataFrame({
            f"{label}": [
                data["cost"].mean(),
                data["cost"].median(),
                data["cost"].min(),
                data["cost"].max()
            ]
        }, index=["Mean", "Median", "Min", "Max"])

    summary_3m = summary_stats(last_3m, "Last 3 Months")
    summary_12m = summary_stats(last_12m, "Last 12 Months")
    summary_table = pd.concat([summary_3m, summary_12m], axis=1)
    st.dataframe(summary_table.style.format("{:.2f}"))

    # --- Visualization: Cost vs Weight using Plotly ---
    st.subheader("Cost evolution")
    df["route"] = df["origin_prefix"] + "→" + df["destination_prefix"]
    fig = px.scatter(
        df,
        x="pickup_date",
        y="cost",
        color="vehicle_type",
        #TODO: Add other relevant columns to hover_data
        hover_data=["route", "contract_type", "weight_kg"],
        title="Cost evolution by Vehicle Type"
    )
    st.plotly_chart(fig, use_container_width=True)

    # -- Visualization: Cost evolution by carrier and shipper ---
    st.subheader("Cost evolution by Carrier and Shipper")

    df["shipper_carrier"] = df["shipper_name"] + "_" + df["carrier_name"]

    # I want to get the pickup month as a string in the format "YYYY-MM"
    df["pickup_year_and_month"] = pd.to_datetime(df["pickup_date"]).dt.strftime('%Y-%m')

    df_grouped = df.groupby(["pickup_year_and_month", "shipper_carrier"]).agg(
        avg_cost=("cost", "mean"),
        median_cost=("cost", "median"),
        min_cost=("cost", "min"),
        max_cost=("cost", "max"),
        count=("cost", "count"),
    ).reset_index()

    # Plot
    fig = px.line(
        df_grouped,
        x="pickup_year_and_month",
        y="avg_cost",
        color="shipper_carrier",
        markers=True,
        title="Average Cost Over Time by Shipper / Carrier",
        labels={"avg_cost": "Avg Cost", "month": "Month"}
    )
    fig.update_layout(xaxis_title="Month", yaxis_title="Average Cost", legend_title="Shipper / Carrier")
    st.plotly_chart(fig, use_container_width=True)

else:
    st.warning("No data matches the selected filters.")
