# streamlit_app.py
import streamlit as st
import pandas as pd
from data_loader import DataLoader
from utils import build_filters_from_widgets

# --- Load external data source ---
st.set_page_config(page_title="Logistics ML Dashboard", layout="wide")
st.title("📦 Logistics Forecast Dashboard")

# Initialize loader (use CSV for now, swap with SQL later)
loader = DataLoader(source="csv", path="data/fake_data.csv")

# Cache unique filter values
# Note: The underscore before the loader parameter is a convention to indicate that Steamlit should not hash the argument
@st.cache_data
def get_filter_options(_loader):
    return {
        "origin_area_name": _loader.get_unique_values("origin_area_name"),
        "vehicle_type": _loader.get_unique_values("vehicle_type"),
        "destination_area_name": _loader.get_unique_values("destination_area_name"),
    }

filter_options = get_filter_options(loader)


# --- Sidebar Filters ---
filters = build_filters_from_widgets(filter_options)

# --- Load and Filter Data ---
st.subheader("Filtered Shipping Data")
data = loader.filter_data(filters)
st.write(data)

# --- Visualization Example: Price vs Weight ---
if not data.empty:
    st.subheader("Shipping costs")
    st.scatter_chart(data=data, x="pickup_start_at_month", y="cost")
else:
    st.warning("No data matches the selected filters.")
