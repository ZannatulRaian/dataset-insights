import io

import pytest
from fastapi.testclient import TestClient

from backend import store
from backend.main import app

client = TestClient(app)

GOOD_CSV = (
    "name,age,score,city\n"
    "Ann,20,80.5,Paris\n"
    "Bob,22,75.0,Rome\n"
    "Cara,21,,Paris\n"
    "Dan,23,90.0,Rome\n"
    "Dan,23,90.0,Rome\n"
    "Eve,25,60.0,Oslo\n"
    "Fay,24,70.0,Oslo\n"
    "Gus,26,85.0,Paris\n"
    "Hal,27,66.0,Rome\n"
    "Ivy,28,95.0,Paris\n"
    "Jon,29,55.0,Oslo\n"
    "Kim,30,88.0,Rome\n"
)


@pytest.fixture(autouse=True)
def _clean_store():
    store.clear()
    yield
    store.clear()


def upload(content=GOOD_CSV, filename="data.csv"):
    return client.post("/upload", files={"file": (filename, io.BytesIO(content.encode()), "text/csv")})


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "healthy"}


def test_index_page_served():
    r = client.get("/")
    assert r.status_code == 200
    assert "Dataset Insights" in r.text


def test_upload_valid_csv():
    r = upload()
    assert r.status_code == 200
    body = r.json()
    assert body["rows"] == 12
    assert body["columns"] == 4
    assert body["quality"]["duplicate_rows"] == 1
    assert body["quality"]["total_missing"] == 1


def test_upload_rejects_non_csv():
    r = upload(filename="data.txt")
    assert r.status_code == 400


def test_upload_rejects_empty_file():
    r = upload(content="")
    assert r.status_code == 400


def test_upload_rejects_headers_only():
    r = upload(content="a,b,c\n")
    assert r.status_code == 400


def test_preview_and_missing_values_are_json_safe():
    ds = upload().json()["dataset_id"]
    r = client.get(f"/dataset/{ds}/preview?rows=5")
    assert r.status_code == 200
    assert len(r.json()["rows"]) == 5


def test_summary_statistics():
    ds = upload().json()["dataset_id"]
    r = client.get(f"/dataset/{ds}/summary")
    assert r.status_code == 200
    body = r.json()
    age = next(c for c in body["numeric"] if c["column"] == "age")
    assert age["min"] == 20 and age["max"] == 30
    assert body["categorical"][0]["column"] in ("name", "city")
    assert len(body["insights"]) >= 2


def test_quality_report():
    ds = upload().json()["dataset_id"]
    q = client.get(f"/dataset/{ds}/quality").json()
    assert q["duplicate_rows"] == 1
    score = next(c for c in q["column_details"] if c["column"] == "score")
    assert score["missing"] == 1


def test_unknown_dataset_returns_404():
    assert client.get("/dataset/nope/summary").status_code == 404


@pytest.mark.parametrize(
    "query",
    [
        "chart=histogram&x=age",
        "chart=bar&x=city",
        "chart=scatter&x=age&y=score",
        "chart=heatmap",
    ],
)
def test_visualizations(query):
    ds = upload().json()["dataset_id"]
    r = client.get(f"/dataset/{ds}/visualizations?{query}")
    assert r.status_code == 200
    assert "data" in r.json()


def test_visualization_rejects_bad_columns():
    ds = upload().json()["dataset_id"]
    assert client.get(f"/dataset/{ds}/visualizations?chart=histogram&x=city").status_code == 400
    assert client.get(f"/dataset/{ds}/visualizations?chart=pie").status_code == 422


def test_prediction():
    ds = upload().json()["dataset_id"]
    r = client.post("/predict", json={"dataset_id": ds, "target": "score", "features": ["age"]})
    assert r.status_code == 200
    body = r.json()
    assert "r2" in body and "mae" in body
    assert body["train_rows"] + body["test_rows"] == 11  # one row has a missing score


def test_prediction_validation():
    ds = upload().json()["dataset_id"]
    r = client.post("/predict", json={"dataset_id": ds, "target": "city", "features": ["age"]})
    assert r.status_code == 400
    r = client.post("/predict", json={"dataset_id": ds, "target": "score", "features": ["score"]})
    assert r.status_code == 400


def test_sample_datasets():
    names = client.get("/samples").json()["samples"]
    assert "students.csv" in names
    r = client.post("/samples/students.csv")
    assert r.status_code == 200
    assert r.json()["rows"] > 100


def test_sample_path_traversal_blocked():
    assert client.post("/samples/..%2F..%2Fetc%2Fpasswd").status_code == 404
    assert client.post("/samples/missing.csv").status_code == 404
