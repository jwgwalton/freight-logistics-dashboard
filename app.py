import streamlit as st
import pandas as pd
import plotly.express as px
from data_loader import load_lane_data, load_model_results, flip_forecast_table
from model import get_forecast_data

st.set_page_config(layout="wide")
st.title("📊 Carrier Cost Forecast Dashboard")

# Sidebar filters
with st.sidebar:
    st.header("2 Digit Lanes")
    country = st.selectbox("Select Country", ["BE", "DE", "FR", "IT", "PL"])
    lanes_df = load_lane_data(country)
    selected_lane = st.selectbox("Select Lane", lanes_df["lane_name"])

    st.markdown("#### Vehicle Type")
    st.write("TRUCK_40_TAUTLINER")

# Main area
st.subheader(f"Forecast: {selected_lane}")
lane_data, charts = load_model_results(selected_lane)

# Display key metrics
st.metric("Total Loads", lane_data["total_loads"])
st.metric("Route Distance", f"{lane_data['distance_km']} km")
st.metric("Sender %", f"{lane_data['sender_pct']:.2f}%")
st.metric("EST %", f"{lane_data['est_pct']:.2f}%")

# Forecast table
st.markdown("### Forecast Table")
# Transposed the dataframe to put the period vertically rather than horizontally
st.dataframe(flip_forecast_table(lane_data["forecast_table"]))

# Forecast plot
st.markdown("### Forecast Trends")
fig = px.line(charts, x="period", y="rate", color="type", markers=True, title="Rate Forecast Over Time")
st.plotly_chart(fig, use_container_width=True)
