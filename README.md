<h2 align="center"> Dataset Insights</h2>

A web app where you upload a CSV file and get data-quality checks, statistics, interactive charts and a simple machine-learning prediction.

**Stack:** Python, FastAPI, Pandas, NumPy, scikit-learn, Plotly.js, HTML/CSS/JavaScript, Pytest, Docker, GitHub Actions.

---

## 1. Software needed


| Software       | Version       | Why                   | Download                                        |
| -------------- | ------------- | --------------------- | ----------------------------------------------- |
| Python         | 3.11 or newer | Runs the backend      | https://www.python.org/downloads/               |
| VS Code        | any           | Code editor           | https://code.visualstudio.com/                  |
| Git            | any           | Version control       | https://git-scm.com/downloads                   |
| Google Chrome  | any           | Use the app           | https://www.google.com/chrome/                  |
| Docker Desktop | optional      | Run it in a container | https://www.docker.com/products/docker-desktop/ |
| GitHub account | optional      | Hosting code and CI   | https://github.com/                             |

**Windows tip:** during the Python install, tick **"Add python.exe to PATH"**.

Verify in a terminal (Command Prompt, PowerShell, or the VS Code terminal):

```
python --version
pip --version
git --version
```

If `python` fails on Windows, use `py` instead. On Mac/Linux use `python3`.

## 2. Set up the project

Unzip the project, then open the `dataset-insights` folder in VS Code (File > Open Folder) and open a terminal inside it.

### Create a virtual environment

Windows (Command Prompt):

```
python -m venv venv
venv\Scripts\activate
```

Windows (PowerShell):

```
python -m venv venv
.\venv\Scripts\Activate.ps1
```

If PowerShell blocks the script, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, or just use Command Prompt.

Mac / Linux:

```
python3 -m venv venv
source venv/bin/activate
```

The prompt should now start with `(venv)`.

### Install dependencies

```
pip install -r requirements.txt
```

## 3. Run the app

From the project root (the folder containing `backend/`):

```
uvicorn backend.main:app --reload
```

Open in Chrome:


| URL                          | What it is                     |
| ---------------------------- | ------------------------------ |
| http://127.0.0.1:8000/       | The web app                    |
| http://127.0.0.1:8000/docs   | Interactive API docs (Swagger) |
| http://127.0.0.1:8000/health | Health check                   |

Stop the server with `Ctrl + C`.

> The charts load Plotly.js from a CDN, so you need an internet connection in the browser.

## 4. How to use it

1. Click **Use sample** (students or sales) or choose your own `.csv` and click **Upload CSV**.
2. Read the overview: rows, columns, missing values, duplicates and plain-English insights.
3. Browse the preview and statistics (mean, median, mode, min, max, std dev).
4. Pick a chart type (histogram, bar, scatter, heatmap) and click **Draw chart**.
5. In **Prediction**, choose a target column (e.g. `exam_score`), tick feature columns (e.g. `study_hours`) and click **Train model**. You get R², MAE, coefficients and an actual-vs-predicted chart.

## 5. Run the tests

```
pytest -v
```

## 6. Run with Docker (optional)

Start Docker Desktop, then:

```
docker build -t dataset-insights .
docker run -p 8000:8000 dataset-insights
```

Open http://localhost:8000.

## 7. Put it on GitHub with CI (optional)

1. Create an empty repository on GitHub (no README).
2. In the project folder:

```
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/<ZannatulRaian>/dataset-insights.git
git push -u origin main
```

3. Open the **Actions** tab. The workflow in `.github/workflows/ci.yml` runs the tests and builds the Docker image on every push.

## 8. Deploy (optional)

The app is a single Docker container, so any container host works. With **Render** (free tier):

1. Push the repo to GitHub.
2. On https://render.com choose **New > Web Service**, connect the repo.
3. Runtime: **Docker**. Render detects the `Dockerfile` and builds it.
4. After deploy, open the URL it gives you. Health check path: `/health`.

(Railway and Fly.io work the same way.)

## 9. Project structure

```
dataset-insights/
├── backend/
│   ├── main.py              App setup, serves the frontend
│   ├── store.py             In-memory dataset storage
│   ├── routes/
│   │   ├── upload.py        POST /upload, sample datasets
│   │   ├── analysis.py      preview, summary, quality, charts
│   │   └── prediction.py    POST /predict
│   └── services/
│       ├── validator.py     File validation + quality report
│       ├── analyzer.py      Statistics and insights
│       ├── visualizer.py    Plotly chart specs
│       └── predictor.py     Linear Regression
├── frontend/                index.html, style.css, script.js
├── tests/test_api.py
├── sample_data/             students.csv, sales.csv
├── Dockerfile
├── .github/workflows/ci.yml
└── requirements.txt
```

## 10. API endpoints


| Method | Endpoint                                 | Purpose                                       |
| ------ | ---------------------------------------- | --------------------------------------------- |
| POST   | `/upload`                                | Upload a CSV, returns a`dataset_id`           |
| GET    | `/samples`                               | List sample datasets                          |
| POST   | `/samples/{name}`                        | Load a sample dataset                         |
| GET    | `/dataset/{id}/preview`                  | First rows                                    |
| GET    | `/dataset/{id}/summary`                  | Statistics and insights                       |
| GET    | `/dataset/{id}/quality`                  | Missing values, duplicates, types             |
| GET    | `/dataset/{id}/columns`                  | Numeric and categorical column names          |
| GET    | `/dataset/{id}/visualizations?chart=...` | Chart data (bar, histogram, scatter, heatmap) |
| POST   | `/predict`                               | Train Linear Regression, return R² and MAE   |

## 11. Troubleshooting


| Problem                        | Fix                                                          |
| ------------------------------ | ------------------------------------------------------------ |
| `python` not found             | Reinstall Python with "Add to PATH", or use`py` / `python3`  |
| `uvicorn` not found            | Activate the venv, then`pip install -r requirements.txt`     |
| `ModuleNotFoundError: backend` | Run uvicorn from the project root, not from inside`backend/` |
| Port 8000 in use               | `uvicorn backend.main:app --reload --port 8001`              |
| Charts don't show              | Check your internet connection (Plotly.js loads from a CDN)  |
| Upload rejected                | File must be a`.csv`, non-empty, under 10 MB                 |

## 12. Design notes

- Uploads are validated by extension, size, emptiness and parseability.
- Sample file names are matched against the real directory listing, which blocks path traversal.
- The frontend writes CSV content with `textContent`, so a malicious CSV cannot inject HTML.
- Datasets live in memory (max 20) and are lost on restart. A database would be the natural next upgrade.

## 13. Ideas to extend

- Excel/JSON upload, download the cleaned data
- More models (Random Forest, Logistic Regression)
- Persist datasets in SQLite or PostgreSQL
- User accounts and saved reports
