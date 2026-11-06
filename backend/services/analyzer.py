"""Statistical analysis and automatic insights."""
import numpy as np
import pandas as pd


def _clean(value):
    """Convert numpy values to JSON-safe Python values (NaN -> None)."""
    if value is None:
        return None
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        return None if np.isnan(value) or np.isinf(value) else round(float(value), 4)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    return value


def numeric_columns(df: pd.DataFrame) -> list:
    return df.select_dtypes(include="number").columns.tolist()


def categorical_columns(df: pd.DataFrame) -> list:
    return df.select_dtypes(exclude="number").columns.tolist()


def preview(df: pd.DataFrame, n: int = 10) -> dict:
    head = df.head(n).astype(object).where(df.head(n).notna(), None)
    records = [{k: _clean(v) for k, v in row.items()} for row in head.to_dict("records")]
    return {"columns": df.columns.tolist(), "rows": records}


def numeric_summary(df: pd.DataFrame) -> list:
    result = []
    for col in numeric_columns(df):
        s = df[col].dropna()
        if s.empty:
            continue
        mode = s.mode()
        result.append(
            {
                "column": col,
                "count": int(s.count()),
                "mean": _clean(s.mean()),
                "median": _clean(s.median()),
                "mode": _clean(mode.iloc[0]) if not mode.empty else None,
                "min": _clean(s.min()),
                "max": _clean(s.max()),
                "std": _clean(s.std()),
            }
        )
    return result


def categorical_summary(df: pd.DataFrame, top_n: int = 5) -> list:
    result = []
    for col in categorical_columns(df):
        s = df[col].dropna()
        counts = s.value_counts().head(top_n)
        result.append(
            {
                "column": col,
                "count": int(s.count()),
                "unique": int(s.nunique()),
                "top": [{"value": str(k), "count": int(v)} for k, v in counts.items()],
            }
        )
    return result


def correlation_matrix(df: pd.DataFrame):
    cols = numeric_columns(df)
    if len(cols) < 2:
        return None
    corr = df[cols].corr()
    return {
        "columns": cols,
        "matrix": [[_clean(v) for v in row] for row in corr.values.tolist()],
    }


def generate_insights(df: pd.DataFrame) -> list:
    """Plain-English findings about the dataset."""
    insights = [f"The dataset has {len(df):,} rows and {df.shape[1]} columns."]

    missing = df.isna().sum()
    worst = missing[missing > 0].sort_values(ascending=False)
    if worst.empty:
        insights.append("No missing values were found.")
    else:
        col, count = worst.index[0], int(worst.iloc[0])
        insights.append(
            f"{int(missing.sum())} values are missing. "
            f"'{col}' has the most ({count}, {count / len(df) * 100:.1f}%)."
        )

    dupes = int(df.duplicated().sum())
    if dupes:
        insights.append(f"{dupes} duplicate row(s) were detected.")

    corr = correlation_matrix(df)
    if corr:
        cols, m = corr["columns"], corr["matrix"]
        best = None
        for i in range(len(cols)):
            for j in range(i + 1, len(cols)):
                v = m[i][j]
                if v is not None and (best is None or abs(v) > abs(best[2])):
                    best = (cols[i], cols[j], v)
        if best and abs(best[2]) >= 0.5:
            direction = "positive" if best[2] > 0 else "negative"
            insights.append(
                f"Strongest relationship: '{best[0]}' and '{best[1]}' "
                f"({direction} correlation, r = {best[2]:.2f})."
            )

    for col in numeric_columns(df):
        s = df[col].dropna()
        if len(s) < 4:
            continue
        q1, q3 = s.quantile(0.25), s.quantile(0.75)
        iqr = q3 - q1
        outliers = int(((s < q1 - 1.5 * iqr) | (s > q3 + 1.5 * iqr)).sum())
        if outliers:
            insights.append(f"'{col}' has {outliers} potential outlier(s).")

    return insights
