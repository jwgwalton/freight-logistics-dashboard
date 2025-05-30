from datetime import datetime, timedelta

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from data_loader import DataLoader

loader = DataLoader(source="csv", path="data/fake_data.csv")

def render():
    filters = {}

    contract_options = loader.get_unique_values("contract_type")
    selected_contract = st.sidebar.selectbox("Contract Type", ["All"] + contract_options)
    if selected_contract != "All":
        filters["contract_type"] = selected_contract

    vehicle_options = loader.get_unique_values("vehicle_type")
    selected_vehicle = st.sidebar.selectbox("Vehicle Type", ["All"] + vehicle_options)
    if selected_vehicle != "All":
        filters["vehicle_type"] = selected_vehicle

    pickup_options = loader.get_unique_prefixes("origin_location_code", filters)
    selected_pickup = st.sidebar.selectbox("Pickup Postcode", ["All"] + pickup_options)
    if selected_pickup != "All":
        filters["origin_location_code"] = selected_pickup + "%"

    delivery_options = loader.get_unique_prefixes("destination_location_code", filters)
    selected_delivery = st.sidebar.selectbox("Delivery Postcode", ["All"] + delivery_options)
    if selected_delivery != "All":
        filters["destination_location_code"] = selected_delivery + "%"

    @st.cache_data
    def load_filtered_data(filters):
        required_columns = [
            "contract_type", "origin_location_code", "destination_location_code", "vehicle_type",
            "weight_kg", "pickup_date", "cost", "carrier_name", "shipper_name"
        ]
        return loader.load_filtered_data(filters, required_columns)

    df = load_filtered_data(filters)

    if not df.empty:
        df["pickup_date"] = pd.to_datetime(df["pickup_date"], errors='coerce')
        min_weight, max_weight = int(df["weight_kg"].min()), int(df["weight_kg"].max())
        if min_weight == max_weight:
            max_weight = min_weight + 1
        weight_range = st.sidebar.slider("Weight Range (kg)", min_weight, max_weight, (min_weight, max_weight))
        df = df[(df["weight_kg"] >= weight_range[0]) & (df["weight_kg"] <= weight_range[1])]

        # -- Summary statistics --
        st.subheader("📊 Price Summary for Last 3 and 12 Months")
        now = datetime.now()
        last_3m = df[df["pickup_date"] >= now - timedelta(days=90)]
        last_12m = df[df["pickup_date"] >= now - timedelta(days=365)]

        def summary_stats(data, label):
            return pd.DataFrame({
                f"{label}": [data["cost"].mean(), data["cost"].median(), data["cost"].min(), data["cost"].max()]
            }, index=["Mean", "Median", "Min", "Max"])

        st.dataframe(pd.concat([
            summary_stats(last_3m, "Last 3 Months"),
            summary_stats(last_12m, "Last 12 Months")
        ], axis=1).style.format("{:.2f}"))

        df["route"] = df["origin_prefix"] + "→" + df["destination_prefix"]

        # -- Cost evolution by Vehicle Type (Scatter plot) --
        st.subheader("Cost evolution")
        fig = px.scatter(
            df, x="pickup_date", y="cost", color="vehicle_type",
            hover_data=["route", "contract_type", "weight_kg"],
            title="Cost evolution by Vehicle Type"
        )
        st.plotly_chart(fig, use_container_width=True)

        # -- Cost evolution by Carrier and Shipper (Overlaid line graphs) --

        st.subheader("Cost evolution by Carrier and Shipper")
        df["shipper_carrier"] = df["shipper_name"] + "_" + df["carrier_name"]
        df["pickup_year_and_month"] = pd.to_datetime(df["pickup_date"]).dt.strftime('%Y-%m')

        df_grouped = df.groupby(["pickup_year_and_month", "shipper_carrier"]).agg(
            avg_cost=("cost", "mean")
        ).reset_index()

        fig = px.line(
            df_grouped, x="pickup_year_and_month", y="avg_cost", color="shipper_carrier", markers=True,
            title="Average Cost Over Time by Shipper / Carrier"
        )
        fig.update_layout(xaxis_title="Month", yaxis_title="Average Cost", legend_title="Shipper / Carrier")
        st.plotly_chart(fig, use_container_width=True)

        # -- Heatmap of Costs by Shipper and Carrier --
        st.subheader("Costs for Carrier and Shipper combinations")
        # Pivot the table to get a heatmap-friendly format
        pivot = df_grouped.pivot(index="shipper_carrier", columns="pickup_year_and_month", values="avg_cost")
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
            title="📊 Average Cost Heatmap (Shipper / Carrier vs Time)",
            xaxis_title="Month",
            yaxis_title="Shipper / Carrier",
            autosize=True,
            # margin=dict(l=100, r=40, t=60, b=60),
            # height=min(800, 40 * len(pivot_df))  # Dynamically set height for large Y labels
        )

        st.plotly_chart(fig, use_container_width=True)


    else:
        st.warning("No data matches the selected filters.")
