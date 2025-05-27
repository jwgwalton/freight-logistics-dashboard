import pandas as pd

class DataLoader:
    def __init__(self, source="csv", path=None, connection=None):
        self.source = source
        self.path = path
        self.connection = connection


    def load_data(self):
        if self.source == "csv":
            return pd.read_csv(self.path)
        elif self.source == "sql":
            if self.connection is None:
                raise ValueError("Database connection is required for SQL source")
            query = "SELECT * FROM shipping_data"
            return pd.read_sql(query, self.connection)
        else:
            raise ValueError("Unsupported data source")

    def get_unique_values(self, column):
        if self.source == "csv":
            df = pd.read_csv(self.path, usecols=[column])
            return df[column].dropna().unique().tolist()
        elif self.source == "sql":
            query = f"SELECT DISTINCT {column} FROM shipping_data"
            df = pd.read_sql(query, self.connection)
            return df[column].dropna().unique().tolist()
        else:
            raise ValueError("Unsupported data source")

    def filter_data(self, filters):
        if self.source == "csv":
            df = pd.read_csv(self.path)
            return self._apply_filters_to_df(df, filters)
        elif self.source == "sql":
            return self._query_with_filters_sql(filters)
        else:
            raise ValueError("Unsupported data source")

    def _apply_filters_to_df(self, df, filters):
        for col, condition in filters.items():
            if "eq" in condition:
                df = df[df[col] == condition["eq"]]
            if "startswith" in condition:
                df = df[df[col].astype(str).str.startswith(condition["startswith"])]
            if "contains" in condition:
                df = df[df[col].astype(str).str.contains(condition["contains"], case=False)]
            if "gte" in condition:
                df = df[df[col] >= condition["gte"]]
            if "lte" in condition:
                df = df[df[col] <= condition["lte"]]
        return df

    def _query_with_filters_sql(self, filters):
        base_query = "SELECT * FROM shipping_data"
        where_clauses = []
        values = []

        for col, condition in filters.items():
            if "eq" in condition:
                where_clauses.append(f"{col} = %s")
                values.append(condition["eq"])
            if "startswith" in condition:
                where_clauses.append(f"{col} LIKE %s")
                values.append(condition["startswith"] + "%")
            if "contains" in condition:
                where_clauses.append(f"{col} ILIKE %s")
                values.append(f"%{condition['contains']}%")
            if "gte" in condition:
                where_clauses.append(f"{col} >= %s")
                values.append(condition["gte"])
            if "lte" in condition:
                where_clauses.append(f"{col} <= %s")
                values.append(condition["lte"])

        if where_clauses:
            full_query = base_query + " WHERE " + " AND ".join(where_clauses)
        else:
            full_query = base_query

        return pd.read_sql(full_query, self.connection, params=values)
