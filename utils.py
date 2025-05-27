from typing import Dict
import streamlit as st

def build_filters_from_widgets(filter_options: Dict[str, list]) -> Dict[str, Dict[str, str]]:
    filters = {}

    pickup = st.sidebar.selectbox("Pickup Postcode", options=filter_options["origin_area_name"])
    filters["origin_area_name"] = {"eq": pickup}

    delivery = st.sidebar.selectbox("Delivery Country", options=filter_options["destination_area_name"])
    filters["destination_area_name"] = {"eq": delivery}

    carrier = st.sidebar.selectbox("Vehicle Type", options=filter_options["vehicle_type"])
    filters["vehicle_type"] = {"eq": carrier}

    weight_range = st.sidebar.slider("Weight Range (kg)", 0, 1000, (0, 1000))
    filters["weight_kg"] = {"gte": weight_range[0], "lte": weight_range[1]}

    return filters
