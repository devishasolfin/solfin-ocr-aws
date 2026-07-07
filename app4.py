import streamlit as st
import json
import pandas as pd
from utils.ocr_engine4 import pipeline_extract

st.set_page_config(page_title="Textract-Llama Pipeline", layout="wide")
st.title("⚡ Non-Bedrock Layout-Agnostic Extractor")
st.caption("Pattern A: Amazon Textract (OCR Line Mapping) + Groq Cloud (Llama 3 Semantic Structuring)")

uploaded_file = st.file_uploader(
    "Upload Utility Bill Image / PDF File",
    type=["pdf", "png", "jpg", "jpeg"]
)

if uploaded_file:
    with st.spinner("Extracting layout strings and calling semantic Llama compiler..."):
        # Launching the structural parsing pipeline
        result = pipeline_extract(uploaded_file)
        
        # Extract raw text before processing the rest of the UI
        raw_text = result.pop("_raw_text", "")
        
        if "error" in result:
            st.error(result["error"])
        else:
            st.success("Document successfully structured into explicit key targets!")
            
            # Create 3 columns: JSON Output, Raw OCR Text, and Data Validation
            col_json, col_raw, col_edit = st.columns([1, 1, 1.2])
            
            with col_json:
                st.subheader("JSON Output Frame")
                st.json(result)
                
                # Download JSON button
                json_data = json.dumps(result, indent=2)
                st.download_button(
                    "Download JSON",
                    json_data,
                    "bill.json",
                    "application/json"
                )
                
            with col_raw:
                st.subheader("Raw OCR Text (Textract)")
                st.text_area("Extracted Lines", raw_text, height=500)
                
            with col_edit:
                st.subheader("Human-In-The-Loop Data Validation")
                
                c1, c2 = st.columns(2)
                with c1:
                    v_name = st.text_input("Name", value=result.get("name"))
                    v_cons = st.text_input("Consumer Number", value=result.get("consumer_number"))
                    v_amt = st.text_input("Total Bill Amount", value=result.get("total_bill_amount"))
                    v_date = st.text_input("Bill Date", value=result.get("bill_date"))
                    v_arr = st.text_input("Arrears Due", value=result.get("arrears"))
                with c2:
                    v_addr = st.text_area("Address", value=result.get("address"), height=68)
                    v_pin = st.text_input("Pincode", value=result.get("pincode"))
                    v_load = st.text_input("Sanction Load", value=result.get("sanction_load"))
                    v_unit = st.text_input("Sanction Load Unit", value=result.get("sanction_load_unit"))
                    v_ucons = st.text_input("Unit Consumed", value=result.get("unit_consumed"))
                    v_rate = st.text_input("Rate Per Unit", value=result.get("rate_per_unit"))
                    
                # Pack modified payload for download data syncing
                validated_payload = {
                    "name": v_name, "consumer_number": v_cons, "total_bill_amount": v_amt,
                    "bill_date": v_date, "arrears": v_arr, "address": v_addr, "pincode": v_pin,
                    "sanction_load": v_load, "sanction_load_unit": v_unit, "unit_consumed": v_ucons,
                    "rate_per_unit": v_rate
                }
                
                st.download_button(
                    label="Download Verified Clean JSON",
                    data=json.dumps(validated_payload, indent=2),
                    file_name="bill_record.json",
                    mime="application/json"
                )
                
                # CSV Download
                df = pd.DataFrame([validated_payload])
                csv = df.to_csv(index=False)
                st.download_button(
                    "Download CSV",
                    csv,
                    "bill.csv",
                    "text/csv"
                )