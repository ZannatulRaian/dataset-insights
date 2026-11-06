from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from backend import store
from backend.services import analyzer, validator, visualizer

router = APIRouter(prefix="/dataset", tags=["Analysis"])


def _get_df(dataset_id: str):
    entry = store.get_dataset(dataset_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="Dataset not found. Upload a file first.")
    return entry["df"]


@router.get("/{dataset_id}/preview")
def preview(dataset_id: str, rows: int = Query(10, ge=1, le=100)):
    return analyzer.preview(_get_df(dataset_id), rows)


@router.get("/{dataset_id}/summary")
def summary(dataset_id: str):
    df = _get_df(dataset_id)
    return {
        "rows": int(df.shape[0]),
        "columns": int(df.shape[1]),
        "numeric": analyzer.numeric_summary(df),
        "categorical": analyzer.categorical_summary(df),
        "insights": analyzer.generate_insights(df),
    }


@router.get("/{dataset_id}/quality")
def quality(dataset_id: str):
    return validator.quality_report(_get_df(dataset_id))


@router.get("/{dataset_id}/visualizations")
def visualizations(
    dataset_id: str,
    chart: str = Query(..., pattern="^(bar|histogram|scatter|heatmap)$"),
    x: Optional[str] = None,
    y: Optional[str] = None,
):
    df = _get_df(dataset_id)
    opts = visualizer.available_options(df)

    if chart == "heatmap":
        fig = visualizer.heatmap(df)
        if fig is None:
            raise HTTPException(status_code=400, detail="Need at least 2 numeric columns for a heatmap.")
        return fig

    if chart == "bar":
        if x not in df.columns:
            raise HTTPException(status_code=400, detail="Choose a valid column for the bar chart.")
        return visualizer.bar_chart(df, x)

    if chart == "histogram":
        if x not in opts["numeric"]:
            raise HTTPException(status_code=400, detail="Choose a numeric column for the histogram.")
        return visualizer.histogram(df, x)

    # scatter
    if x not in opts["numeric"] or y not in opts["numeric"]:
        raise HTTPException(status_code=400, detail="Choose two numeric columns for the scatter plot.")
    return visualizer.scatter_plot(df, x, y)


@router.get("/{dataset_id}/columns")
def columns(dataset_id: str):
    return visualizer.available_options(_get_df(dataset_id))
