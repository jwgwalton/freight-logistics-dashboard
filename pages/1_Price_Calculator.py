import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from data_loader import DataLoader, FilterType

st.title("📊 Pricing Model Dashboard")

loader = DataLoader(source="csv", path="data/fake_data.csv")

with st.form("lookup_form"):
    st.markdown("Enter shipment details to estimate median cost over the last 3 months.")

    input_vehicle = st.selectbox("Vehicle Type", [""] + loader.get_unique_values("vehicle_type"))
    input_origin = st.text_input("Pickup Prefix (e.g., 'NW1')").upper()
    input_dest = st.text_input("Delivery Prefix (e.g., 'E14')").upper()
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
            "origin_location_code": f"{input_origin}%",
            "destination_location_code": f"{input_dest}%",
            "pickup_date": (three_months_ago.strftime("%Y-%m-%d"), now.strftime("%Y-%m-%d"), FilterType.DATE),
            "weight_kg": (input_weight * (1-percentage_variance_for_weight), input_weight * (1+percentage_variance_for_weight), FilterType.RANGE),  # ±10% weight range
        }

        df_lookup = loader.load_filtered_data(filters, required_columns=["pickup_date", "cost"])

        if not df_lookup.empty:
            median_price = df_lookup["cost"].median()
            st.success(f"Estimated median cost for similar shipments (last 3 months): **£{median_price:.2f}**")
            st.dataframe(df_lookup[["pickup_date", "origin_location_code", "destination_location_code", "weight_kg", "cost"]])
        else:
            a_year_ago = now - timedelta(days=365)
            new_filters = {
                "vehicle_type": input_vehicle,
                "origin_location_code": f"{input_origin}%",  # match prefix
                "destination_location_code": f"{input_dest}%", # match prefix
                "pickup_date": (a_year_ago.strftime("%Y-%m-%d"), now.strftime("%Y-%m-%d"), FilterType.DATE),
            }
            weight_removed_df_lookup = loader.load_filtered_data(new_filters, required_columns=["pickup_date", "weight_kg", "origin_location_code", "destination_location_code",  "cost"])
            if not weight_removed_df_lookup.empty:
                st.warning("No shipments found with similar weight in the last 3 months. Showing results over the last 12 months:")
                st.dataframe(weight_removed_df_lookup[["pickup_date", "origin_location_code", "destination_location_code", "weight_kg", "cost"]])
            else:
                st.error("No shipments found in the last 12 months between the selected locations and vehicle type. Please try different criteria.")
