
import os

import pandas as pd
import requests
import streamlit as st

# Base URL of the Flask backend ("backend" is the backend container name on the Docker network)
BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:7860")

# Columns the model expects (same as the backend API)
REQUIRED_COLUMNS = [
    "Product_Weight", "Product_Sugar_Content", "Product_Allocated_Area", "Product_MRP",
    "Store_Size", "Store_Location_City_Type", "Store_Type", "Product_Id_char",
    "Store_Age_Years", "Product_Type_Category",
]

# Product type -> (Product_Id prefix, category), as derived in the training notebook
PRODUCT_TYPES = {
    "Baking Goods": ("FD", "Non Perishables"),
    "Breads": ("FD", "Perishables"),
    "Breakfast": ("FD", "Perishables"),
    "Canned": ("FD", "Non Perishables"),
    "Dairy": ("FD", "Perishables"),
    "Frozen Foods": ("FD", "Non Perishables"),
    "Fruits and Vegetables": ("FD", "Perishables"),
    "Meat": ("FD", "Perishables"),
    "Seafood": ("FD", "Perishables"),
    "Snack Foods": ("FD", "Non Perishables"),
    "Starchy Foods": ("FD", "Non Perishables"),
    "Hard Drinks": ("DR", "Non Perishables"),
    "Soft Drinks": ("DR", "Non Perishables"),
    "Health and Hygiene": ("NC", "Non Perishables"),
    "Household": ("NC", "Non Perishables"),
    "Others": ("NC", "Non Perishables"),
}

# Known SuperKart stores (store age computed with reference year 2025, as in training)
STORES = {
    "OUT001 - Supermarket Type1, Tier 2": {"Store_Size": "High", "Store_Location_City_Type": "Tier 2",
                                           "Store_Type": "Supermarket Type1", "Store_Age_Years": 38},
    "OUT002 - Food Mart, Tier 3": {"Store_Size": "Small", "Store_Location_City_Type": "Tier 3",
                                   "Store_Type": "Food Mart", "Store_Age_Years": 27},
    "OUT003 - Departmental Store, Tier 1": {"Store_Size": "Medium", "Store_Location_City_Type": "Tier 1",
                                            "Store_Type": "Departmental Store", "Store_Age_Years": 26},
    "OUT004 - Supermarket Type2, Tier 2": {"Store_Size": "Medium", "Store_Location_City_Type": "Tier 2",
                                           "Store_Type": "Supermarket Type2", "Store_Age_Years": 16},
}
CUSTOM_STORE = "Custom store"


def error_message(response):
    """Extract the error message returned by the API (or fall back to the raw text)."""
    try:
        return response.json().get("error", response.text)
    except ValueError:
        return response.text


st.set_page_config(page_title="SuperKart Sales Forecast", page_icon="🛒", layout="wide")
st.title("🛒 SuperKart Sales Forecast")
st.write("Forecast the total sales of a product in a SuperKart store, for a single product or a whole CSV file.")

single_tab, batch_tab = st.tabs(["Single prediction", "Batch prediction"])

# ---------------------------------------------------------------- Single prediction
with single_tab:
    product_col, store_col = st.columns(2)

    with product_col:
        st.subheader("Product details")
        product_type = st.selectbox("Product Type", list(PRODUCT_TYPES), index=list(PRODUCT_TYPES).index("Frozen Foods"))
        product_id_char, product_type_category = PRODUCT_TYPES[product_type]
        st.caption(f"Product ID prefix: **{product_id_char}** · Category: **{product_type_category}**")
        # Non-consumables (NC) are always "No Sugar"; food and drinks are "Low Sugar" or "Regular"
        sugar_options = ["No Sugar"] if product_id_char == "NC" else ["Low Sugar", "Regular"]
        product_sugar_content = st.selectbox("Product Sugar Content", sugar_options)
        product_weight = st.number_input("Product Weight", min_value=0.0, max_value=50.0, value=12.66, step=0.1)
        product_mrp = st.number_input("Product MRP", min_value=0.0, max_value=1000.0, value=117.08, step=1.0)
        product_allocated_area = st.number_input(
            "Product Allocated Area (share of store display area)",
            min_value=0.0, max_value=1.0, value=0.027, step=0.001, format="%.3f",
        )

    with store_col:
        st.subheader("Store details")
        store_choice = st.selectbox("Store", list(STORES) + [CUSTOM_STORE], index=3)
        if store_choice == CUSTOM_STORE:
            store = {
                "Store_Size": st.selectbox("Store Size", ["Small", "Medium", "High"]),
                "Store_Location_City_Type": st.selectbox("Store Location City Type", ["Tier 1", "Tier 2", "Tier 3"]),
                "Store_Type": st.selectbox("Store Type", ["Supermarket Type1", "Supermarket Type2", "Departmental Store", "Food Mart"]),
                "Store_Age_Years": st.number_input("Store Age (Years)", min_value=0, max_value=100, value=10),
            }
            st.info("Combinations not seen in the historical data are extrapolations; treat these forecasts with care.")
        else:
            store = STORES[store_choice]
            st.table(pd.DataFrame({"Value": {k: str(v) for k, v in store.items()}}))

    product_data = {
        "Product_Weight": product_weight,
        "Product_Sugar_Content": product_sugar_content,
        "Product_Allocated_Area": product_allocated_area,
        "Product_MRP": product_mrp,
        "Product_Id_char": product_id_char,
        "Product_Type_Category": product_type_category,
        **store,
    }

    if st.button("Predict Sales", type="primary"):
        try:
            response = requests.post(f"{BACKEND_URL}/v1/predict", json=product_data, timeout=30)
        except requests.exceptions.RequestException as e:
            st.error(f"Unable to connect to the prediction API at {BACKEND_URL}: {e}")
        else:
            if response.status_code == 200:
                st.metric("Predicted Product Store Sales Total", f"{response.json()['Sales']:,.2f}")
            else:
                st.error(f"Prediction failed ({response.status_code}): {error_message(response)}")

# ---------------------------------------------------------------- Batch prediction
with batch_tab:
    st.subheader("Batch Prediction")
    st.write("Upload a CSV file with the columns: " + ", ".join(f"`{c}`" for c in REQUIRED_COLUMNS))

    uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])

    if uploaded_file is not None:
        try:
            batch_df = pd.read_csv(uploaded_file)
        except Exception as e:
            st.error(f"Could not read the file as CSV: {e}")
            st.stop()

        missing = [c for c in REQUIRED_COLUMNS if c not in batch_df.columns]
        if missing:
            st.error(f"The file is missing required column(s): {', '.join(missing)}")
            st.stop()

        st.write(f"Preview ({len(batch_df)} rows):")
        st.dataframe(batch_df.head(), use_container_width=True)

        if st.button("Predict for Batch", type="primary"):
            csv_bytes = batch_df.to_csv(index=False).encode("utf-8")
            try:
                response = requests.post(
                    f"{BACKEND_URL}/v1/predictbatch",
                    files={"file": ("batch.csv", csv_bytes, "text/csv")},
                    timeout=120,
                )
            except requests.exceptions.RequestException as e:
                st.error(f"Unable to connect to the prediction API at {BACKEND_URL}: {e}")
            else:
                if response.status_code == 200:
                    # The API returns {"row index": predicted sales}
                    predictions = response.json()
                    results = batch_df.copy()
                    results["Predicted_Sales"] = [predictions[str(i)] for i in range(len(batch_df))]
                    st.session_state["batch_results"] = results
                else:
                    st.session_state.pop("batch_results", None)
                    st.error(f"Batch prediction failed ({response.status_code}): {error_message(response)}")

        # Results are kept in session state so they stay visible after the download button is clicked
        if "batch_results" in st.session_state:
            results = st.session_state["batch_results"]
            st.success(f"Predictions completed for {len(results)} rows.")
            st.metric("Total predicted sales", f"{results['Predicted_Sales'].sum():,.2f}")
            st.dataframe(results, use_container_width=True)
            st.download_button(
                "Download predictions as CSV",
                data=results.to_csv(index=False).encode("utf-8"),
                file_name="superkart_batch_predictions.csv",
                mime="text/csv",
            )
