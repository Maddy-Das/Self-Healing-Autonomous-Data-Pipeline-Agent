import pandas as pd
from pathlib import Path


def profile_csv(file_path: str) -> dict:
    """
    Analyze a CSV file and return a structured data profile.
    Used by the Builder Agent to understand the data before generating pipeline code.
    """
    path = Path(file_path)
    df = pd.read_csv(path, low_memory=False)

    columns = []
    for col in df.columns:
        col_data = df[col]
        dtype = str(col_data.dtype)

        # Determine semantic type
        if "int" in dtype:
            semantic_type = "integer"
        elif "float" in dtype:
            semantic_type = "float"
        elif "datetime" in dtype:
            semantic_type = "datetime"
        elif "bool" in dtype:
            semantic_type = "boolean"
        else:
            # Check if it could be a date
            try:
                pd.to_datetime(col_data.dropna().head(20))
                semantic_type = "datetime_string"
            except (ValueError, TypeError):
                semantic_type = "string"

        col_info = {
            "name": col,
            "dtype": dtype,
            "semantic_type": semantic_type,
            "null_count": int(col_data.isnull().sum()),
            "null_percent": round(float(col_data.isnull().mean() * 100), 2),
            "unique_count": int(col_data.nunique()),
            "sample_values": [str(v) for v in col_data.dropna().head(5).tolist()],
        }

        # Add numeric stats
        if semantic_type in ("integer", "float"):
            col_info["min"] = float(col_data.min()) if not col_data.isnull().all() else None
            col_info["max"] = float(col_data.max()) if not col_data.isnull().all() else None
            col_info["mean"] = round(float(col_data.mean()), 2) if not col_data.isnull().all() else None
            col_info["std"] = round(float(col_data.std()), 2) if not col_data.isnull().all() else None

        columns.append(col_info)

    # Duplicate detection
    duplicate_count = int(df.duplicated().sum())

    profile = {
        "file_name": path.name,
        "row_count": len(df),
        "column_count": len(df.columns),
        "duplicate_rows": duplicate_count,
        "columns": columns,
        "sample_rows": df.head(5).fillna("NULL").to_dict(orient="records"),
    }

    return profile
