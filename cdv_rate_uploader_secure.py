
import streamlit as st
import pandas as pd
import requests
import json
import io

# === App Configuration ===
st.set_page_config(page_title="CDV Rate Uploader", layout="centered")
st.title("📈 Update CDV Rates in Customer.io")

# === Secure Secret Config ===
API_KEY = st.secrets["API_KEY"]
COLLECTION_ID = 5
API_URL = f"https://api.customer.io/v1/api/collections/{COLLECTION_ID}/content"

# === User Inputs ===
uploaded_file = st.file_uploader("Upload the CD Rates CSV", type="csv")
object_ids_input = st.text_input("Enter object_id values (comma-separated):")

submit = st.button("Start Upload")

if submit and uploaded_file and object_ids_input:
    with st.spinner("Processing and uploading..."):
        # === Load and clean data ===
        df = pd.read_csv(uploaded_file, low_memory=False)
        df.columns = df.columns.str.strip().str.lower()
        df.dropna(axis=1, how="all", inplace=True)

        # === Parse IDs ===
        selected_ids = [x.strip() for x in object_ids_input.split(",")]

        # === Transform into Collection Schema ===
        payload = []
        for idx, oid in enumerate(selected_ids):
            row = df[df["object_id"] == oid]
            if row.empty:
                st.warning(f"object_id {oid} not found.")
                continue
            row = row.iloc[0]

            # Determine legal text
            legal_text = ""
            if pd.notna(row.get("certno")) and str(row.get("certno")).strip() != "":
                legal_text = "Member FDIC"
            elif pd.notna(row.get("ncuano")) and str(row.get("ncuano")).strip() != "":
                legal_text = "Insured by NCUA"

            # Format min_dep with commas
            raw_min = row.get("minbalance", "")
            try:
                formatted_min = "${:,}".format(int(float(raw_min)))
            except:
                formatted_min = f"${raw_min}"

            payload.append({
                "id": str(idx),
                "rate_id": oid,
                "bank_name": row.get("bankname", ""),
                "bank_link": row.get("bankdetailsurl", ""),
                "bank_logo_url": row.get("banklogo", ""),
                "rate": row.get("apy", ""),
                "term": f"{row.get('terminmonths', '')} Month",
                "legal": legal_text,
                "min_dep": f"{formatted_min} min deposit"
            })

        # === API Call ===
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }

        response = requests.put(API_URL, headers=headers, data=json.dumps(payload))

        if response.status_code == 200:
            st.success("✅ Rates collection successfully updated!")
        else:
            st.error(f"❌ Failed to update collection. Status: {response.status_code}")
            st.text(response.text)
