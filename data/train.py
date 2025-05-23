import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler, FunctionTransformer
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.metrics import mean_absolute_error
import mlflow
import mlflow.sklearn



df = pd.read_csv("data/dummy_data.csv")

# Extract postcode area (e.g., 'SW1A' → 'SW')
def extract_postcode_area(df):
    df = df.copy()
    df["Pickup_Area"] = df["Pickup_Postcode"].str.extract(r"^([A-Z]{1,2}\d{1,2})")
    df["Delivery_Area"] = df["Delivery_Postcode"].str.extract(r"^([A-Z]{1,2}\d{1,2})")
    return df[["Pickup_Area", "Delivery_Area", "Weight_kg", "Carrier_Type"]]

# Define transformers
preprocessor = ColumnTransformer([
    ("onehot", OneHotEncoder(handle_unknown="ignore"), ["Pickup_Area", "Delivery_Area", "Carrier_Type"]),
    ("scale", StandardScaler(), ["Weight_kg"])
])

# Full pipeline
pipeline = Pipeline([
    ("feature_engineering", FunctionTransformer(extract_postcode_area, validate=False)),
    ("preprocessing", preprocessor),
    ("regressor", RandomForestRegressor(n_estimators=100, random_state=42))
])

# Split data
X = df.drop(columns=["Cost_EUR"])
y = df["Cost_EUR"]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)


with mlflow.start_run():
    print("Training the model")
    # Fit model
    pipeline.fit(X_train, y_train)

    # Predict and evaluate
    preds = pipeline.predict(X_test)
    print("MAE:", mean_absolute_error(y_test, preds))

    mlflow.sklearn.save_model(pipeline, "model")