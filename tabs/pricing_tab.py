import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from data_loader import DataLoader, FilterType

loader = DataLoader(source="csv", path="data/fake_data.csv")

def render():
    st.title("📊 Pricing Model Dashboard")

    with st.form("lookup_form"):
        st.markdown("Enter shipment details to estimate median cost over the last 3 months.")

        input_vehicle = st.selectbox("Vehicle Type", [""] + loader.get_unique_values("vehicle_type"))
        input_origin = st.text_input("Pickup Prefix (e.g., 'NW1')").upper()
        input_dest = st.text_input("Delivery Prefix (e.g., 'E14')").upper()
        input_weight = st.number_input("Weight (kg)", min_value=0.0, value=10.0, step=0.5)

        submitted = st.form_submit_button("Estimate")
        if submitted:
            now = datetime.now()
            three_months_ago = now - timedelta(days=90)

            filters = {
                "vehicle_type": input_vehicle,
                "origin_location_code": f"{input_origin}%",
                "destination_location_code": f"{input_dest}%",
                "pickup_date": (three_months_ago.strftime("%Y-%m-%d"), now.strftime("%Y-%m-%d"), FilterType.DATE),
                "weight_kg": (input_weight * 0.9, input_weight * 1.1, FilterType.RANGE),
            }

            df_lookup = loader.load_filtered_data(filters, required_columns=["pickup_date", "cost"])

            if not df_lookup.empty:
                median_price = df_lookup["cost"].median()
                st.success(f"Estimated median cost for similar shipments (last 3 months): **\u00a3{median_price:.2f}**")
                st.dataframe(df_lookup)
            else:
                a_year_ago = now - timedelta(days=365)
                new_filters = {
                    "vehicle_type": input_vehicle,
                    "origin_location_code": f"{input_origin}%",
                    "destination_location_code": f"{input_dest}%",
                    "pickup_date": (a_year_ago.strftime("%Y-%m-%d"), now.strftime("%Y-%m-%d"), FilterType.DATE),
                }
                weight_removed_df = loader.load_filtered_data(new_filters, required_columns=["pickup_date", "cost"])
                if not weight_removed_df.empty:
                    st.warning("No similar-weight shipments in last 3 months. Showing last 12 months instead.")
                    st.dataframe(weight_removed_df)
                else:
                    st.error("No data found for the criteria. Try changing filters.")
