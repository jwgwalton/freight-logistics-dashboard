import streamlit as st
import mlflow

@st.cache_resource
def load_model():
    return mlflow.sklearn.load_model("model")

model = load_model()


def get_forecast_data(lane_id):
    # Load or compute forecast data (e.g., using a pre-trained ML model)
    # Return DataFrame: columns=["period", "type", "rate"]
    pass

