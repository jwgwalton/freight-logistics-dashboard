import pandas as pd
import numpy as np
from faker import Factory
import random

# Initialize faker and seed
fake = Factory.create('en_GB')
np.random.seed(42)
random.seed(42)


# Define fake UK postcodes
def generate_postcode():
    return fake.postcode()


# Service and carrier types
service_types = ["Express", "Standard", "Economy"]
carrier_types = ["Marketplace", "Dedication", "EST"]


# Generate synthetic data
def generate_shipping_data(n_rows=1000):
    data = []
    for _ in range(n_rows):
        pickup = generate_postcode()
        delivery = generate_postcode()
        distance_km = round(np.random.uniform(20, 800), 1)
        weight_kg = round(np.random.uniform(1, 200), 1)
        service = random.choice(service_types)
        carrier = random.choice(carrier_types)
        date = fake.date_between(start_date='-6M', end_date='today')

        # Cost based on distance, weight, and service
        base_rate = 0.8 + 0.2 * service_types.index(service)  # Express is most expensive
        cost = round(base_rate * distance_km * (0.8 + 0.4 * (weight_kg / 100)), 2)

        data.append({
            "Pickup_Postcode": pickup,
            "Delivery_Postcode": delivery,
            "Distance_km": distance_km,
            "Weight_kg": weight_kg,
            "Service_Type": service,
            "Carrier_Type": carrier,
            "Date": date,
            "Cost_EUR": cost
        })

    return pd.DataFrame(data)


# Generate test dataset
shipping_df = generate_shipping_data(500)

# Show first few rows
print(shipping_df.head())

shipping_df.to_csv("data/dummy_data.csv")
