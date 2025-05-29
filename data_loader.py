from typing import List
import polars as pl
import pandas as pd


# Mapping of frontend column names to database or CSV file column names.
# Key: Column name in the frontend
# Value: Column name in the database or CSV file
FRONT_END_TO_BACKEND_COLUMN_MAPPING = {
    "origin_location_code": "backend_origin_location_code",
    "destination_location_code": "backend_destination_location_code",
    # These are not taken from the bakend, but derived from the location codes
    # "origin_prefix": "backend_origin_prefix",
    # "destination_prefix": "backend_destination_prefix",
    "vehicle_type": "backend_vehicle_type",
    "weight_kg": "backend_weight_kg",
    "pickup_date": "backend_pickup_date",
    "cost": "backend_cost"
}

# For mapping from backend to frontend after gathering data
BACKEND_TO_FRONT_END_COLUMN_MAPPING = {v: k for k, v in FRONT_END_TO_BACKEND_COLUMN_MAPPING.items()}

class DataLoader:
    def __init__(self, source="csv", path=None, table=None, conn_str=None):
        self.source = source
        self.path = path
        self.table = table
        self.conn_str = conn_str
        self.df = None

        if self.source == "csv" and self.path:
            self.df = pl.read_csv(self.path)
        elif self.source == "sql" and self.conn_str and self.table:
            # SQL connection logic would go here, but is not implemented yet
            raise NotImplementedError("SQL support is not implemented for Polars backend yet.")

    def load_filtered_data(self, filters, required_columns=None) -> pd.DataFrame:
        if self.source == "csv":
            df = self.df

            # Select only necessary columns
            needed_columns = set(filters.keys())
            if required_columns:
                needed_columns.update(required_columns)

            # Add columns needed for prefix derivation
            needed_columns.update({"origin_location_code", "destination_location_code"})

            # Map from display names to the ones in the database/csv
            mapped_needed_columns = {col: FRONT_END_TO_BACKEND_COLUMN_MAPPING.get(col, col) for col in needed_columns}

            # Gather the columns from the database/csv
            df = df.select(list(mapped_needed_columns))

            # Rename columns based on mapping, So the frontend can use the same names regardless of the source names
            df = df.rename({col: BACKEND_TO_FRONT_END_COLUMN_MAPPING[col] for col in mapped_needed_columns})

            # Data enrichment: Convert date columns to datetime
            # Add derived columns for prefix
            df = df.with_columns([
                pl.col("origin_location_code").cast(str).str.slice(0, 3).alias("origin_prefix"),
                pl.col("destination_location_code").cast(str).str.slice(0, 3).alias("destination_prefix")
            ])

            # Apply filters
            for col, val in filters.items():
                if isinstance(val, tuple) and len(val) == 2:
                    print("Column:", col, "Value:", val)
                    df = df.filter(pl.col(col).is_between(val[0], val[1]))
                elif isinstance(val, str) and "%" in val:
                    pattern = val.replace("%", "")
                    df = df.filter(pl.col(col).cast(str).str.starts_with(pattern))
                else:
                    df = df.filter(pl.col(col) == val)

            # Convert to pandas DataFrame for compatibility with the frontend
            df: pd.Dataframe = df.to_pandas()

            return df
        else:
            raise NotImplementedError("SQL support is not implemented for Polars backend yet.")

    def get_unique_values(self, column, filters=None) -> List[str]:
        df = self.df

        column = FRONT_END_TO_BACKEND_COLUMN_MAPPING[column]

        # Apply filters if needed
        if filters:
            # Map the frontend column names to the database/csv column names
            mapped_filters = {FRONT_END_TO_BACKEND_COLUMN_MAPPING[col]: val for col, val in filters.items()}
            for col, val in mapped_filters.items():
                if isinstance(val, tuple) and len(val) == 2:
                    df = df.filter(pl.col(col).is_between(val[0], val[1]))
                elif isinstance(val, str) and "%" in val:
                    pattern = val.replace("%", "")
                    df = df.filter(pl.col(col).cast(str).str.contains(pattern, literal=False))
                else:
                    df = df.filter(pl.col(col) == val)

        return sorted(df.select(column).unique().to_series().to_list())
