"""Validation of uploaded files and data quality reporting."""
import io

import pandas as pd

MAX_FILE_SIZE_MB = 10
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
MAX_ROWS = 200_000
MAX_COLUMNS = 200


class ValidationError(Exception):
    """Raised when an uploaded file is not acceptable."""


def validate_and_parse(filename: str, content: bytes) -> pd.DataFrame:
    """Check an uploaded file and return it as a DataFrame."""
    if not filename or not filename.lower().endswith(".csv"):
        raise ValidationError("Only .csv files are supported.")
    if len(content) == 0:
        raise ValidationError("The uploaded file is empty.")
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise ValidationError(f"File is too large. Maximum size is {MAX_FILE_SIZE_MB} MB.")

    try:
        df = pd.read_csv(io.BytesIO(content))
    except pd.errors.EmptyDataError:
        raise ValidationError("The CSV file has no data.")
    except (pd.errors.ParserError, UnicodeDecodeError):
        raise ValidationError("Could not parse the file as a valid CSV.")

    if df.empty:
        raise ValidationError("The CSV file has headers but no rows.")
    if len(df) > MAX_ROWS:
        raise ValidationError(f"Too many rows. Maximum is {MAX_ROWS:,}.")
    if df.shape[1] > MAX_COLUMNS:
        raise ValidationError(f"Too many columns. Maximum is {MAX_COLUMNS}.")

    df.columns = [str(c).strip() for c in df.columns]
    return df


def quality_report(df: pd.DataFrame) -> dict:
    """Missing values, duplicates and column types."""
    total_cells = int(df.shape[0] * df.shape[1])
    missing_per_col = df.isna().sum()
    total_missing = int(missing_per_col.sum())
    duplicate_rows = int(df.duplicated().sum())

    columns = []
    for col in df.columns:
        missing = int(missing_per_col[col])
        columns.append(
            {
                "column": col,
                "dtype": str(df[col].dtype),
                "missing": missing,
                "missing_percent": round(missing / len(df) * 100, 2),
                "unique": int(df[col].nunique(dropna=True)),
            }
        )

    return {
        "rows": int(df.shape[0]),
        "columns": int(df.shape[1]),
        "total_missing": total_missing,
        "missing_percent": round(total_missing / total_cells * 100, 2) if total_cells else 0,
        "duplicate_rows": duplicate_rows,
        "column_details": columns,
    }
