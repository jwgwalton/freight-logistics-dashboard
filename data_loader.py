import polars as pl
import pandas as pd

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
            df = df.select(list(needed_columns))

            #TODO: Add data enrichment logic here, strip it out of the generate_fake_data
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

            return df.to_pandas()
        else:
            raise NotImplementedError("SQL support is not implemented for Polars backend yet.")

    def get_unique_values(self, column, filters=None):
        df = self.df

        # Apply filters if needed
        if filters:
            for col, val in filters.items():
                if isinstance(val, tuple) and len(val) == 2:
                    df = df.filter(pl.col(col).is_between(val[0], val[1]))
                elif isinstance(val, str) and "%" in val:
                    pattern = val.replace("%", "")
                    df = df.filter(pl.col(col).cast(str).str.contains(pattern, literal=False))
                else:
                    df = df.filter(pl.col(col) == val)

        return sorted(df.select(column).unique().to_series().to_list())
