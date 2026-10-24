# SuperKart Sales Forecasting

Containerised deployment of the SuperKart product-store sales forecasting model.

| Folder | Contents |
|---|---|
| `backend/` | Flask REST API (`app.py`), serialized model pipeline (`superkart_model.joblib`), `requirements.txt`, `Dockerfile` (port 7860) |
| `frontend/` | Streamlit UI (`app.py`), `requirements.txt`, `Dockerfile` (port 8501) |
| `sample_data/` | `Batch_Data_SuperKart.csv` for testing batch inference |

## Run in GitHub Codespaces

```bash
bash run_containers.sh
```

Then open the **Ports** tab, set ports **7860** and **8501** to *Public*, and open the forwarded URL of port 8501.

## API

- `GET /health` -> `{"status": "ok"}`
- `POST /v1/predict` - JSON body with the 10 model features -> `{"Sales": <float>}`
- `POST /v1/predictbatch` - CSV file under form key `file` -> `{"<row index>": <float>, ...}`
