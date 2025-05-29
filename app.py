import streamlit as st
import pandas as pd

from data_loader import DataLoader
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

# Step 1: Carrier Type
carrier_options = loader.get_unique_values("vehicle_type")
selected_carrier = st.sidebar.selectbox("Carrier Type", ["All"] + carrier_options)
if selected_carrier != "All":
    filters["vehicle_type"] = selected_carrier

# Step 2: Delivery Country (dependent on carrier type)
delivery_options = loader.get_unique_values("destination_prefix", filters)
selected_country = st.sidebar.selectbox("Delivery Postcode", ["All"] + delivery_options)
if selected_country != "All":
    filters["destination_prefix"] = selected_country

# Step 3: Pickup Postcode (dependent on above filters)
pickup_options = loader.get_unique_values("origin_prefix", filters)
selected_pickup = st.sidebar.selectbox("Pickup Postcode", ["All"] + pickup_options)
if selected_pickup != "All":
    filters["origin_prefix"] = selected_pickup

# Step 4: Load filtered data
@st.cache_data
def load_filtered_data(filters):
    required_columns = [
        "origin_prefix",
        "destination_prefix",
        "vehicle_type",
        "weight_kg",
        "pickup_date",
        "cost"
    ]
    return loader.load_filtered_data(filters, required_columns)

df = load_filtered_data(filters)

# --- Add extra fields ---
if not df.empty:
    df["pickup_date"] = pd.to_datetime(df["pickup_date"], errors='coerce')

    # Weight filter
    min_weight, max_weight = int(df["weight_kg"].min()), int(df["weight_kg"].max())
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
        hover_data=["route"],
        title="Cost evolution by Vehicle Type"
    )
    st.plotly_chart(fig, use_container_width=True)

else:
    st.warning("No data matches the selected filters.")

st.markdown("---")
st.subheader("🔍 Forecast Lookup")

with st.form("lookup_form"):
    st.markdown("Enter shipment details to estimate median cost over the last 3 months.")

    input_vehicle = st.selectbox("Vehicle Type", [""] + loader.get_unique_values("vehicle_type"))
    input_origin = st.text_input("Origin Prefix (e.g., 'NW1')").upper()
    input_dest = st.text_input("Destination Prefix (e.g., 'E14')").upper()
    input_weight = st.number_input("Weight (kg)", min_value=0.0, value=10.0, step=0.5)

    # Validation check
    all_filled = (
        input_vehicle != "" and
        input_origin != "" and
        input_dest != "" and
        input_weight > 0
    )

    submitted = st.form_submit_button("Estimate")#, disabled=not all_filled)
    if submitted:
        # --- Apply filters ---
        # Only look at the last 3 months`
        now = datetime.now()
        three_months_ago = now - timedelta(days=90)
        # Only look at ±10% variance for weight
        percentage_variance_for_weight = 0.1  # 10% variance

        filters = {
            "vehicle_type": input_vehicle,
            # These are the actual column names in the data
            "origin_location_code": f"{input_origin}%",  # match prefix
            "destination_location_code": f"{input_dest}%",
            #"pickup_date": (three_months_ago.strftime("%Y-%m-%d"), now.strftime("%Y-%m-%d")),
            "weight_kg": (input_weight * (1-percentage_variance_for_weight), input_weight * (1+percentage_variance_for_weight)),  # ±10% weight range
        }

        df_lookup = loader.load_filtered_data(filters, required_columns=["pickup_date", "cost"])

        if not df_lookup.empty:
            median_price = df_lookup["cost"].median()
            st.success(f"Estimated median cost for similar shipments (last 3 months): **£{median_price:.2f}**")
            st.dataframe(df_lookup[["pickup_date", "origin_location_code", "destination_location_code", "weight_kg", "cost"]])
        else:
            st.warning("No similar shipments found for the entered criteria.")
            new_filters = {
                "vehicle_type": input_vehicle,
                # These are the actual column names in the data
                "origin_location_code": f"{input_origin}%",  # match prefix
                "destination_location_code": f"{input_dest}%",
                # "pickup_date": (three_months_ago.strftime("%Y-%m-%d"), now.strftime("%Y-%m-%d")),
                # "weight_kg": (input_weight * (1 - percentage_variance_for_weight),
                #               input_weight * (1 + percentage_variance_for_weight)),  # ±10% weight range
            }
            weight_removed_df_lookup = loader.load_filtered_data(new_filters, required_columns=["weight_kg", "origin_location_code", "destination_location_code",  "cost"])
            if not weight_removed_df_lookup.empty:
                st.warning("No shipments found with the exact weight, but here are similar shipments:")
                st.dataframe(weight_removed_df_lookup[["origin_location_code", "destination_location_code", "weight_kg", "cost"]])
            else:
                st.error("No shipments found for the search with the weight criteria removed")


