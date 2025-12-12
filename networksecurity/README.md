
# NetworkSecurity_ML

**Machine Learning based Phishing & Malicious URL Detection**

This repository implements an end-to-end ML pipeline for detecting malicious network/URL data. It contains components for data ingestion from MongoDB, validation, preprocessing (KNN imputation), model training (several classical ML classifiers), and a FastAPI service to serve predictions.

---

## Quick summary (what this project does)

- Reads raw records from a MongoDB collection and exports them to CSV (feature store).  
- Splits data into train/test and validates schema & data drift.  
- Applies preprocessing (KNN imputation), transforms data into numpy arrays.  
- Trains ML models (RandomForest, DecisionTree, LogisticRegression, AdaBoost) with GridSearchCV and tracks experiments with MLflow / DagsHub.  
- Saves trained model and preprocessor artifacts to `final_model/` and artifact folders.  
- Provides a FastAPI app (`app.py`) with:
  - `GET /` → redirects to `/docs`
  - `GET /train` → runs the full training pipeline (ingestion → validation → transformation → training)
  - `POST /predict` → accepts a CSV upload, runs preprocessing + model prediction, returns HTML table with predictions.

---

## Repo structure (based on the files you provided)

```
.
├── app.py                     # FastAPI server for training & prediction
├── main.py                    # Script to run the pipeline (ingest → validate → transform → train)
├── push_data.py               # Helper to convert CSV to JSON and push records to MongoDB
├── test_mongodb.py            # Small script to test MongoDB connectivity (contains hardcoded URI — remove in prod)
├── requirements.txt
├── templates/
│   └── table.html             # Jinja2 HTML template used by /predict response (expected)
├── final_model/               # produced artifacts: preprocessor.pkl, model.pkl
└── networksecurity/           # package containing components, utils, entities, constants
    ├── components/
    │   ├── dataingestion.py
    │   ├── data_validation.py
    │   ├── data_tranformation.py
    │   └── model_trainer.py
    ├── constant/
    │   └── training_pipeline.py
    ├── entity/
    ├── exception/
    ├── logging/
    └── utils/
```

---

## Important environment variables

The code expects environment variables loaded from a `.env` file:

- `MONGO_DB_URL`  
  - used by `push_data.py` and data ingestion component to connect with MongoDB.
- `MONGODB_URL_KEY`  
  - used by `app.py` (note: variable name differs from `MONGO_DB_URL` — keep both in `.env` or standardize).

**Example `.env`:**
```
MONGO_DB_URL="mongodb+srv://<username>:<password>@cluster0.example.mongodb.net/?retryWrites=true&w=majority"
MONGODB_URL_KEY="mongodb+srv://<username>:<password>@cluster0.example.mongodb.net/?retryWrites=true&w=majority"
```

> ⚠️ **Security note:** Do **not** commit secrets (usernames/passwords) to the repository. Remove any hard-coded credentials (e.g., `test_mongodb.py` contains a literal URI) before sharing the repo publicly.

---

## Setup and installation

1. Create a virtual environment (recommended) and activate it:
```bash
python -m venv venv
source venv/bin/activate   # macOS / Linux
venv\Scripts\activate      # Windows
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file (see above) with your MongoDB connection string.

4. Ensure `templates/table.html` exists (used by FastAPI `/predict` to render result).

---

## How to use

### 1) Push CSV data to MongoDB (optional)
`push_data.py` reads a local CSV file and inserts the records into the configured MongoDB database & collection.

```bash
python push_data.py
```

By default (in the script) the file path is:
```
FILE_PATH = "Network_Data\\phisingData.csv"
DATABASE = "PHISING_DB"
Collection = "NetworkData"
```
Modify the script variables or pass your own CSV path before running.

---

### 2) Run the pipeline (from `main.py`)

This runs the pipeline sequentially:
- Data ingestion (reads from MongoDB)
- Data validation (schema & drift checks)
- Data transformation (KNN imputation & save preprocessor)
- Model training (GridSearchCV over several classifiers)

```bash
python main.py
```

Artifacts (CSV, numpy arrays, saved objects) will be stored under the `artifact/` directory (timestamped) as configured in `networksecurity/constant/training_pipeline.py`.

---

### 3) Start the API server (`app.py`)

This starts a FastAPI server (defaults to host `localhost`, port `6000` when run direct). Two important endpoints:

- Start training via HTTP:
  ```
  GET http://localhost:6000/train
  ```
  This will run the whole training pipeline (same as `main.py`) and return "Training is successful" on success.

- Prediction endpoint:
  ```
  POST http://localhost:6000/predict
  Content-Type: multipart/form-data
  Form field: file   (attach a CSV file)
  ```
  The CSV is read into a DataFrame, preprocessor `final_model/preprocessor.pkl` and `final_model/model.pkl` are loaded, predictions are added as `predicted_column` and an HTML table is returned.

Start server locally:
```bash
python app.py
# or use uvicorn for development
uvicorn app:app --host 0.0.0.0 --port 6000 --reload
```

---

## Expected input format for `/predict`

- Upload a CSV that contains the same feature columns used for training (i.e., same columns as in the `feature_store` output / training CSV).
- The application expects the preprocessor saved at `final_model/preprocessor.pkl` and model at `final_model/model.pkl`.

---

## ML details

- **Preprocessing:** `DataTransformation` uses a `KNNImputer` inside an sklearn `Pipeline`. The pipeline object is saved both to `artifact/...` and to `final_model/preprocessor.pkl`.
- **Modeling:** `ModelTrainer` tries several models (RandomForest, DecisionTree, LogisticRegression, AdaBoost) and uses `evaluate_models` (GridSearchCV) to select the best model based on `r2_score` computed on test set predictions (note: classification metrics use f1/precision/recall for logged results — consider using classification scores consistently).
- **Model wrapper:** `NetworkModel` applies the preprocessor transform, then `model.predict(...)` to generate predictions.
- **Metrics:** `get_classification_score` computes f1/precision/recall and these are logged via MLflow/DagsHub.

---

## Files of interest (short descriptions)

- `networksecurity/components/dataingestion.py`  
  - Connects to MongoDB, fetches collection into pandas DataFrame, replaces "na" with NaN, saves feature store CSV and splits into train/test.

- `networksecurity/components/data_validation.py`  
  - Reads YAML schema (`SCHEMA_FILE_PATH`), validates number of columns & presence of numerical columns, runs Kolmogorov–Smirnov test for data drift, writes drift report as YAML.

- `networksecurity/components/data_tranformation.py`  
  - Fits `KNNImputer` on train features, transforms train/test, concatenates target column (target mapping replaces -1 with 0), saves transformed numpy arrays and pickles the preprocessor.

- `networksecurity/components/model_trainer.py`  
  - Performs hyperparameter tuning using `GridSearchCV`, picks best model using test `r2_score`, wraps and saves model using `NetworkModel`, saves `final_model/model.pkl`.

- `app.py`  
  - FastAPI app for running pipeline and serving predictions. Uses `pymongo` to connect (via `MONGODB_URL_KEY`) and Jinja2 to render results.

- `push_data.py`  
  - Utility to read CSV and insert many documents into a MongoDB collection. Useful to seed the MongoDB collection for ingestion step.

---
 

 

