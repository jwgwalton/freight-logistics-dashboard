import streamlit as st
import pandas as pd

from data_loader import DataLoader
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- Streamlit Setup ---
st.set_page_config(page_title="Carrier pricing Dashboard", layout="wide")
st.title("Carrier pricing Dashboard")

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

carrier_options = loader.get_unique_values("vehicle_type")
selected_carrier = st.sidebar.selectbox("Carrier Type", ["All"] + carrier_options)
if selected_carrier != "All":
    filters["vehicle_type"] = selected_carrier

pickup_options = loader.get_unique_prefixes("origin_location_code", filters)
selected_pickup = st.sidebar.selectbox("Pickup Postcode", ["All"] + pickup_options)
if selected_pickup != "All":
    filters["origin_location_code"] = selected_pickup  + "%" # Match the prefix in the whole postcode

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
        "pickup_date",
        "cost",
        "carrier_name",
        "shipper_name",
    ]
    return loader.load_filtered_data(filters, required_columns)

df = load_filtered_data(filters)


def estimate_price(df: pd.DataFrame) -> int:
    """
    Estimate price based on origin, destination
    """
    #TODO: You could implement a more sophisticated estimation here
    # Remove outliers
    # Filter for the las
    median_price = df["cost"].median()
    return median_price

# --- Display Filtered Data ---
if not df.empty:
    price = estimate_price(df)
    st.success(f"Estimated Price based on selected filters: £{price}")

    df["pickup_date"] = pd.to_datetime(df["pickup_date"], errors='coerce')


    # --- Summary Table for Last 3 and 12 Months ---
    now = datetime.now()
    last_3m = df[df["pickup_date"] >= now - timedelta(days=90)]
    last_12m = df[df["pickup_date"] >= now - timedelta(days=365)]

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

    # ONly show the summary table if there are results in the last 3 or 12 months
    if not summary_table.isna().all().all():
        st.subheader("📊 Price Summary for Last 3 and 12 Months")
        st.dataframe(summary_table.style.format("{:.2f}"))


    # -- Cost evolution by Vehicle Type (Scatter plot) --
    st.subheader("Historical data")
    df["route"] = df["origin_prefix"] + "→" + df["destination_prefix"]
    fig = px.scatter(
        df, x="pickup_date", y="cost", color="vehicle_type",
        hover_data=["route", "contract_type"],
        title="Cost evolution by Vehicle Type"
    )
    st.plotly_chart(fig, use_container_width=True)


    # -- Cost evolution by Carrier and Shipper (Overlaid line graphs) --

    st.subheader("Costs variance by Carrier")
    df["pickup_year_and_month"] = pd.to_datetime(df["pickup_date"]).dt.strftime('%Y-%m')

    df_grouped = df.groupby(["pickup_year_and_month", "carrier_name"]).agg(
        avg_cost=("cost", "mean")
    ).reset_index()

    fig = px.line(
        df_grouped, x="pickup_year_and_month", y="avg_cost", color="carrier_name", markers=True,
        title="Average Cost Over Time by Shipper / Carrier"
    )
    fig.update_layout(xaxis_title="Month", yaxis_title="Average Cost", legend_title="Carrier")
    st.plotly_chart(fig, use_container_width=True)

    # -- Heatmap of Costs by Shipper and Carrier --
    # Pivot the table to get a heatmap-friendly format
    pivot = df_grouped.pivot(index="carrier_name", columns="pickup_year_and_month", values="avg_cost")
    # Create Plotly heatmap
    fig = go.Figure(
        data=go.Heatmap(
            z=pivot.values,
            x=pivot.columns.tolist(),
            y=pivot.index.tolist(),
            colorscale="Viridis",
            colorbar=dict(title="Avg Cost (£)")
        )
    )

    fig.update_layout(
        title="📊 Average Cost Heatmap (Carrier vs Time)",
        xaxis_title="Month",
        yaxis_title="Shipper / Carrier",
        autosize=True,
        # margin=dict(l=100, r=40, t=60, b=60),
        # height=min(800, 40 * len(pivot_df))  # Dynamically set height for large Y labels
    )

    st.plotly_chart(fig, use_container_width=True)

else:
    st.warning("No data matches the selected filters.")