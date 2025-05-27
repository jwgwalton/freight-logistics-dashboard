from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import streamlit as st

from data_loader import DataLoader

# --- Streamlit Setup ---
st.set_page_config(page_title="Logistics Pricing Dashboard", layout="wide")
st.title("📦 Logistics Pricing Dashboard")

# --- Initialize Data Loader ---
loader = DataLoader(source="csv", path="data/fake_data.csv")

# --- Load and Cache Full Dataset ---
@st.cache_data
def load_full_data():
    return loader.load_data()

full_data = load_full_data()

# --- Progressive Filtering ---
df = full_data.copy()

df["pickup_prefix"] = df["origin_location_code"].astype(str).str[:3]
df["delivery_prefix"] = df["destination_location_code"].astype(str).str[:3]
df["pickup_date"] = pd.to_datetime(df["pickup_date"], errors="coerce")

# Filter 1: Carrier Type
carrier_types = df["vehicle_type"].dropna().unique()
selected_carrier = st.sidebar.selectbox("Carrier Type", ["All"] + sorted(carrier_types))
if selected_carrier != "All":
    df = df[df["vehicle_type"] == selected_carrier]

# Filter 2: Delivery Country (depends on selected carrier)
delivery_options = df["delivery_prefix"].dropna().unique()
selected_country = st.sidebar.selectbox("Delivery Postcode", ["All"] + sorted(delivery_options))
if selected_country != "All":
    df = df[df["delivery_prefix"] == selected_country]

# Filter 3: Pickup Postcode (depends on previous)
pickup_options = df["pickup_prefix"].dropna().unique()
selected_pickup = st.sidebar.selectbox("Pickup Postcode", ["All"] + sorted(pickup_options))
if selected_pickup != "All":
    df = df[df["pickup_prefix"] == selected_pickup]

# # Filter 4: Weight Range
if not df.empty:
    min_weight, max_weight = int(df["weight_kg"].min()), int(df["weight_kg"].max())
    weight_range = st.sidebar.slider("Weight Range (kg)", min_value=min_weight, max_value=max_weight, value=(min_weight, max_weight))
    df = df[(df["weight_kg"] >= weight_range[0]) & (df["weight_kg"] <= weight_range[1])]

# --- Display Filtered Data ---
if not df.empty:
    # --- Summary Table for Last 3 and 12 Months ---
    if len(df) > 1:
        st.subheader("Price Summary for Last 3 and 12 Months")
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
        st.dataframe(summary_table.style.format("{:.2f}"))

    # --- Visualizations ---
    st.subheader("Shipping costs")
    df["route"] = df["pickup_prefix"] + " → " + df["delivery_prefix"]
    fig = px.scatter(
        df,
        x="pickup_date",
        y="cost",
        color="vehicle_type",
        hover_data=["route", "cost"],
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("No data matches the selected filters.")


