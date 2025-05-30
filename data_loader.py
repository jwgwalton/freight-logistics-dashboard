from typing import List, Dict, Any, Optional
from enum import Enum
import polars as pl
import pandas as pd

class FilterType(Enum):
    DATE = "date"
    RANGE = "range"

FRONT_END_TO_BACKEND_COLUMN_MAPPING = {
    "origin_location_code": "backend_origin_location_code",
    "destination_location_code": "backend_destination_location_code",
    "vehicle_type": "backend_vehicle_type",
    "weight_kg": "backend_weight_kg",
    "pickup_date": "backend_pickup_date",
    "contract_type": "backend_contract_type",
    "cost": "backend_cost",
    "carrier_name": "backend_carrier_name",
    "shipper_name": "backend_shipper_name",
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
            self.df = pl.read_csv(self.path).lazy()
        elif self.source == "sql":
            raise NotImplementedError("SQL support is not implemented for Polars backend yet.")

    def _apply_filters(self, df: pl.LazyFrame, filters: Dict[str, Any], use_front_end_names=False) -> pl.LazyFrame:
        """
        Apply filters to the DataFrame based on the provided filter dictionary.
        The filters can include:
        - date ranges (tuples with two values)
        - string prefixes (e.g., "prefix%")
        - exact matches (single values)
        """
        for col, val in filters.items():
            col_name = col if use_front_end_names else FRONT_END_TO_BACKEND_COLUMN_MAPPING[col]

            if isinstance(val, tuple) and len(val) == 3:
                if isinstance(val, tuple) and len(val) == 3:
                    start, end, filter_type = val
                    if filter_type == FilterType.DATE:
                        df = df.with_columns(
                            pl.col(col_name).cast(pl.Date)
                        )
                        df = df.filter(
                            (pl.col(col_name) >= pl.lit(start).str.to_date()) &
                            (pl.col(col_name) <= pl.lit(end).str.to_date())
                        )
                    elif filter_type == FilterType.RANGE:
                        df = df.filter(pl.col(col_name).is_between(start, end))
                    else:
                        raise ValueError(f"Unknown filter type '{filter_type}' for column '{col}'")
            elif isinstance(val, str) and val.endswith('%'):
                df = df.filter(pl.col(col_name).cast(pl.Utf8).str.starts_with(val[:-1]))
            else:
                df = df.filter(pl.col(col_name) == val)
        return df

    def load_filtered_data(self, filters: Dict[str, Any], required_columns: Optional[List[str]] = None) -> pd.DataFrame:
        df = self.df

        # Ensure we include all columns needed for filtering or return
        needed_columns = set(filters.keys())
        if required_columns:
            needed_columns.update(required_columns)

        # Map column names
        mapped_needed_columns = {col: FRONT_END_TO_BACKEND_COLUMN_MAPPING.get(col, col) for col in needed_columns}
        columns_to_select = list(mapped_needed_columns.values())

        # Add required columns for prefixes (computed lazily)
        origin_col = FRONT_END_TO_BACKEND_COLUMN_MAPPING["origin_location_code"]
        dest_col = FRONT_END_TO_BACKEND_COLUMN_MAPPING["destination_location_code"]
        df = df.with_columns([
            pl.col(origin_col).cast(pl.Utf8).str.slice(0, 3).alias("origin_prefix"),
            pl.col(dest_col).cast(pl.Utf8).str.slice(0, 3).alias("destination_prefix")
        ])

        # Apply filters before selection to minimize data loaded
        df = self._apply_filters(df, filters, use_front_end_names=False)

        # Select only required columns + prefixes
        final_cols = list(set(columns_to_select + ["origin_prefix", "destination_prefix"]))
        df = df.select(final_cols)

        # Rename back to frontend names
        rename_map = {v: k for k, v in FRONT_END_TO_BACKEND_COLUMN_MAPPING.items() if v in df.collect_schema()}
        df = df.rename(rename_map)

        return df.collect().to_pandas()

    def get_unique_values(self, column: str, filters: Optional[Dict[str, Any]] = None) -> List[str]:
        backend_col = FRONT_END_TO_BACKEND_COLUMN_MAPPING[column]
        df = self.df
        if filters:
            df = self._apply_filters(df, filters, use_front_end_names=False)
        return sorted(df.select(pl.col(backend_col).unique()).collect().to_series().to_list())

    def get_unique_prefixes(self, column: str, filters: Optional[Dict[str, Any]] = None, prefix_len: int = 3) -> List[str]:
        if column not in ["origin_location_code", "destination_location_code"]:
            raise ValueError("Column must be 'origin_location_code' or 'destination_location_code'")
        backend_col = FRONT_END_TO_BACKEND_COLUMN_MAPPING[column]
        prefix_col = f"{column}_prefix"

        df = self.df
        if filters:
            df = self._apply_filters(df, filters, use_front_end_names=False)

        df = df.with_columns([
            pl.col(backend_col).cast(pl.Utf8).str.slice(0, prefix_len).alias(prefix_col)
        ])
        return sorted(df.select(pl.col(prefix_col).unique()).collect().to_series().to_list())
