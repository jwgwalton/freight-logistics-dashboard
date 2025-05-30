from typing import List, Dict, Any, Optional
import polars as pl
import pandas as pd

FRONT_END_TO_BACKEND_COLUMN_MAPPING = {
    "origin_location_code": "backend_origin_location_code",
    "destination_location_code": "backend_destination_location_code",
    "vehicle_type": "backend_vehicle_type",
    "weight_kg": "backend_weight_kg",
    "pickup_date": "backend_pickup_date",
    "cost": "backend_cost"
}

BACKEND_TO_FRONT_END_COLUMN_MAPPING = {v: k for k, v in FRONT_END_TO_BACKEND_COLUMN_MAPPING.items()}

class DataLoader:
    def __init__(self, source: str = "csv", path: Optional[str] = None, table: Optional[str] = None, conn_str: Optional[str] = None):
        self.source = source
        self.path = path
        self.table = table
        self.conn_str = conn_str
        self.df = None

        if self.source == "csv" and self.path:
            self.df = pl.read_csv(self.path)
        elif self.source == "sql" and self.conn_str and self.table:
            raise NotImplementedError("SQL support is not implemented for Polars backend yet.")

    def _apply_filters(self, df: pl.DataFrame, filters: Dict[str, Any], use_front_end_names=False) -> pl.DataFrame:
        for col, val in filters.items():
            col_name = col if use_front_end_names else FRONT_END_TO_BACKEND_COLUMN_MAPPING[col]

            # Handle range filter (e.g. weight or pickup_date)
            if isinstance(val, tuple) and len(val) == 2:
                df = df.filter(pl.col(col_name).is_between(val[0], val[1]))
            # Handle prefix-based string filter (e.g. "NW1%")
            elif isinstance(val, str) and val.endswith('%'):
                prefix = val[:-1]
                df = df.filter(pl.col(col_name).cast(pl.Utf8).str.starts_with(prefix))
            # Exact match
            else:
                df = df.filter(pl.col(col_name) == val)

        return df

    def load_filtered_data(self, filters: Dict[str, Any], required_columns: Optional[List[str]] = None) -> pd.DataFrame:
        df = self.df

        needed_columns = set(filters.keys())
        if required_columns:
            needed_columns.update(required_columns)

        # We need to ensure the columns are present so we can then filter by them
        df = df.with_columns([
            pl.col(FRONT_END_TO_BACKEND_COLUMN_MAPPING["origin_location_code"]).cast(str).str.slice(0, 3).alias("origin_prefix"),
            pl.col(FRONT_END_TO_BACKEND_COLUMN_MAPPING["destination_location_code"]).cast(str).str.slice(0, 3).alias("destination_prefix")
        ])

        mapped_needed_columns = {col: FRONT_END_TO_BACKEND_COLUMN_MAPPING.get(col, col) for col in needed_columns}

        # Add the prefixes as they are used in the frontend
        columns_to_return = list(mapped_needed_columns.values()) + ["origin_prefix", "destination_prefix"]
        df = df.select(columns_to_return)
        df = df.rename({v: k for k, v in mapped_needed_columns.items() if v in df.columns})

        df = self._apply_filters(df, filters, use_front_end_names=True)
        return df.to_pandas()

    def get_unique_values(self, column: str, filters: Optional[Dict[str, Any]] = None) -> List[str]:
        df = self.df
        backend_col = FRONT_END_TO_BACKEND_COLUMN_MAPPING[column]
        if filters:
            df = self._apply_filters(df, filters, use_front_end_names=False)
        return sorted(df.select(backend_col).unique().to_series().to_list())

    def get_unique_prefixes(self, column: str, filters: Optional[Dict[str, Any]] = None, prefix_len: int = 3, ) -> list[
        str]:
        df = self.df
        if filters:
            df = self._apply_filters(df, filters, use_front_end_names=False)

        prefix_col = f"{column}_prefix"
        #TODO: Work out why the polars version didn't work
        pd_df = df.to_pandas()
        pd_df[prefix_col] = pd_df[FRONT_END_TO_BACKEND_COLUMN_MAPPING[column]].apply(lambda x: x[0:int(prefix_len)])
        return sorted(pd_df[prefix_col].unique().tolist())