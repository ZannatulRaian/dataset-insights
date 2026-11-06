"""Builds Plotly figure specs as plain JSON (the browser renders them).

Using plain dicts means the backend does not need the plotly package;
the frontend loads plotly.js from a CDN.
"""
import pandas as pd

from backend.services.analyzer import correlation_matrix, numeric_columns


def bar_chart(df: pd.DataFrame, column: str, top_n: int = 15) -> dict:
    counts = df[column].astype(str).value_counts().head(top_n)
    return {
        "data": [{"type": "bar", "x": counts.index.tolist(), "y": [int(v) for v in counts.values]}],
        "layout": {"title": f"Top values in {column}", "xaxis": {"title": column}, "yaxis": {"title": "Count"}},
    }


def histogram(df: pd.DataFrame, column: str) -> dict:
    values = df[column].dropna().tolist()
    return {
        "data": [{"type": "histogram", "x": values, "nbinsx": 20}],
        "layout": {"title": f"Distribution of {column}", "xaxis": {"title": column}, "yaxis": {"title": "Frequency"}},
    }


def scatter_plot(df: pd.DataFrame, x: str, y: str) -> dict:
    sub = df[[x, y]].dropna()
    if len(sub) > 5000:
        sub = sub.sample(5000, random_state=42)
    return {
        "data": [{"type": "scatter", "mode": "markers", "x": sub[x].tolist(), "y": sub[y].tolist()}],
        "layout": {"title": f"{y} vs {x}", "xaxis": {"title": x}, "yaxis": {"title": y}},
    }


def heatmap(df: pd.DataFrame):
    corr = correlation_matrix(df)
    if corr is None:
        return None
    return {
        "data": [
            {
                "type": "heatmap",
                "z": corr["matrix"],
                "x": corr["columns"],
                "y": corr["columns"],
                "zmin": -1,
                "zmax": 1,
                "colorscale": "RdBu",
                "reversescale": True,
            }
        ],
        "layout": {"title": "Correlation heatmap"},
    }


def available_options(df: pd.DataFrame) -> dict:
    """Which columns can be used for which chart."""
    num = numeric_columns(df)
    cat = [c for c in df.columns if c not in num]
    return {"numeric": num, "categorical": cat}
