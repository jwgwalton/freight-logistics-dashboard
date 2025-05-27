import pandas as pd
import numpy as np
import random
from faker import Faker
from datetime import datetime, timedelta

# Initialize faker
fake = Faker('en_GB')  # Use UK locale for consistency with UK country codes
Faker.seed(42)
np.random.seed(42)

# Constants
num_rows = 100000
eu_countries = ['DE', 'FR', 'NL', 'BE', 'PL', 'IT', 'ES', 'AT', 'CZ', 'HU', 'RO']
uk_country = ['GB']
all_countries = uk_country #+ eu_countries

# Helper functions
def generate_route():
    origin_country = random.choice(all_countries)
    destination_country = random.choice(all_countries)
    is_domestic = origin_country == destination_country
    origin_lat = round(np.random.uniform(50.0, 60.0), 6)
    origin_lon = round(np.random.uniform(-5.0, 10.0), 6)
    destination_lat = round(np.random.uniform(45.0, 60.0), 6)
    destination_lon = round(np.random.uniform(-5.0, 15.0), 6)
    route_distance_km = round(np.random.uniform(50, 1500), 1)
    cost = (route_distance_km * 1.5) + np.random.uniform(0.0, 10.0)
    return {
        "origin_country_code": origin_country,
        "destination_country_code": destination_country,
        "is_domestic_load": int(is_domestic),
        "origin_latitude": origin_lat,
        "origin_longitude": origin_lon,
        "destination_latitude": destination_lat,
        "destination_longitude": destination_lon,
        "origin_area_name": fake.city(),
        "destination_area_name": fake.city(),
        "origin_location_code": fake.postcode(),
        "destination_location_code": fake.postcode(),
        "route_distance_km": route_distance_km,
        "weight_kg": round(np.random.uniform(0, 1000), 1),
        "cost": cost
    }

# Generate data
data = []

for _ in range(num_rows):
    start_date = fake.date_between(start_date='-3y', end_date='-1m')

    row = {
        "pickup_date": start_date,
        # "pickup_start_at_month": pickup_start.month,
        # "pickup_start_at_week": pickup_start.isocalendar()[1],
        # "pickup_start_at_day": pickup_start.day,
        # "pickup_start_at_hour": pickup_start.hour,
        # "diff_days_carrier_locked_at_pickup_start_at": diff_days,
        "contract_type": random.choice(["spot", "tender"]),
        "vehicle_type": random.choice(["van", "truck", "mega", "refrigerated"]),
        "multistop_count": random.randint(0, 3),
        "is_roundtrip": random.choice([0, 1])
    }
    row.update(generate_route())
    data.append(row)

df = pd.DataFrame(data)

# Save to CSV
df.to_csv('data/fake_data.csv', index=False)