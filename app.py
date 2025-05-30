import streamlit as st
from tabs import overview_tab, pricing_tab

st.set_page_config(page_title="Logistics ML Dashboard", layout="wide")
st.title("🚞 Logistics Forecast Dashboard")

# Create top-level tabs
tab1, tab2 = st.tabs(["📊 Overview", "📈 Pricing Model"])

with tab1:
    overview_tab.render()

with tab2:
    pricing_tab.render()