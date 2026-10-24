
# Import necessary libraries
import joblib  # For loading the serialized model
import pandas as pd  # For data manipulation
from flask import Flask, request, jsonify  # For creating the Flask API

# Initialize Flask app with a name
superkart_api = Flask("SuperKart")
# Keep batch predictions in row order (Flask sorts JSON keys alphabetically by default: "0", "1", "10", "2", ...)
superkart_api.json.sort_keys = False

# Load the trained model pipeline (preprocessing + regressor)
model = joblib.load("superkart_model.joblib")

# Features expected by the model, in the exact order used during training
FEATURES = list(model.feature_names_in_)
NUMERIC_FEATURES = ["Product_Weight", "Product_Allocated_Area", "Product_MRP", "Store_Age_Years"]


def prepare_input(df):
    """Validate the input columns/values and return (clean_dataframe, error_message)."""
    missing = [col for col in FEATURES if col not in df.columns]
    if missing:
        return None, f"Missing required field(s): {', '.join(missing)}"

    # Keep only the model features, in training order (extra columns are ignored)
    df = df[FEATURES].copy()

    for col in NUMERIC_FEATURES:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    invalid = [col for col in FEATURES if df[col].isnull().any()]
    if invalid:
        return None, f"Missing or non-numeric value(s) in: {', '.join(invalid)}"

    negative = [col for col in NUMERIC_FEATURES if (df[col] < 0).any()]
    if negative:
        return None, f"Value(s) must be non-negative in: {', '.join(negative)}"

    for col in FEATURES:
        if col not in NUMERIC_FEATURES:
            df[col] = df[col].astype(str).str.strip()
    return df, None


# Define a route for the home page
@superkart_api.get('/')
def home():
    return "Welcome to the SuperKart Sales Forecasting API"


# Health check endpoint, useful to verify the container is up
@superkart_api.get('/health')
def health():
    return jsonify({"status": "ok"})


# Define an endpoint to predict sales for a single product
@superkart_api.post('/v1/predict')
def predict_sales():
    # Get JSON data from the request
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Request body must be a JSON object with the product and store details"}), 400

    # Validate the input and convert it into a single-row DataFrame
    input_data, error = prepare_input(pd.DataFrame([data]))
    if error:
        return jsonify({"error": error}), 400

    # Make a prediction using the trained model
    try:
        prediction = float(model.predict(input_data)[0])
    except Exception as e:
        return jsonify({"error": f"Prediction failed: {e}"}), 500

    # Return the prediction as a JSON response
    return jsonify({"Sales": round(prediction, 2)})


# Define an endpoint to predict sales for a batch of products
@superkart_api.post('/v1/predictbatch')
def predict_sales_batch():
    # Get the uploaded CSV file from the request
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded. Send a CSV file under the form key 'file'"}), 400

    # Read the file into a DataFrame
    try:
        raw_data = pd.read_csv(request.files['file'])
    except Exception as e:
        return jsonify({"error": f"Could not read the uploaded file as CSV: {e}"}), 400
    if raw_data.empty:
        return jsonify({"error": "The uploaded CSV file has no rows"}), 400

    input_data, error = prepare_input(raw_data)
    if error:
        return jsonify({"error": error}), 400

    # Make predictions for the batch data
    try:
        predictions = model.predict(input_data)
    except Exception as e:
        return jsonify({"error": f"Prediction failed: {e}"}), 500

    # Create an output dictionary mapping row index to predicted sales
    output_dict = {str(i): round(float(pred), 2) for i, pred in enumerate(predictions)}
    return jsonify(output_dict)


# Run the Flask development server when executed directly (gunicorn is used inside the container)
if __name__ == '__main__':
    superkart_api.run(host="0.0.0.0", port=7860)
