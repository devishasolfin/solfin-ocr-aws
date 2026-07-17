import streamlit as st
import json
import pandas as pd
from utils.ocr_engine13 import pipeline_extract

st.set_page_config(page_title="Textract-Llama Pipeline", layout="wide")
st.title("Solfin Layout-Agnostic Extractor")
st.caption("Pattern A: Amazon Textract (Analyze Document: Forms + Tables) + Groq Cloud (Llama 3 Semantic Structuring)")

uploaded_file = st.file_uploader(
    "Upload Utility Bill Image / PDF File",
    type=["pdf", "png", "jpg", "jpeg"]
)

if uploaded_file:
    with st.spinner("Extracting layout strings (Forms/Tables) and calling semantic Llama compiler..."):
        # Launching the structural parsing pipeline
        result = pipeline_extract(uploaded_file)
        
        # Extract raw text before processing the rest of the UI
        raw_text = result.pop("_raw_text", "")
        
        if "error" in result:
            st.error(result["error"])
            if "details" in result:
                st.caption(result["details"])
        else:
            st.success("Document successfully structured into explicit key targets!")
            
            # Display Overall Confidence Metric
            overall_conf = result.get("overall_confidence", 0.0)
            st.metric("Overall Extraction Confidence", f"{overall_conf * 100:.1f}%")
            
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
                st.subheader("Raw OCR Text (Textract Analyze)")
                st.text_area("Extracted Forms, Tables & Lines", raw_text, height=500)
                
            with col_edit:
                st.subheader("Human-In-The-Loop Data Validation")
                
                conf_scores = result.get("confidence_scores", {})
                
                # Helper to format label with confidence score
                def fmt_label(label, key):
                    score = conf_scores.get(key, 0.0)
                    return f"{label} ({score * 100:.0f}% Conf.)"
                
                c1, c2 = st.columns(2)
                with c1:
                    # Note: Cleaned up trailing spaces in dictionary keys to prevent empty UI fields
                    v_name = st.text_input(fmt_label("Name", "name"), value=result.get("name", ""))
                    v_cons = st.text_input(fmt_label("Consumer Number", "consumer_number"), value=result.get("consumer_number", ""))
                    v_amt = st.text_input(fmt_label("Total Bill Amount", "total_bill_amount"), value=result.get("total_bill_amount", ""))
                    v_date = st.text_input(fmt_label("Bill Date", "bill_date"), value=result.get("bill_date", ""))
                    v_arr = st.text_input(fmt_label("Arrears Due", "arrears"), value=result.get("arrears", ""))
                with c2:
                    v_addr = st.text_area(fmt_label("Address", "address"), value=result.get("address", ""), height=68)
                    v_pin = st.text_input(fmt_label("Pincode", "pincode"), value=result.get("pincode", ""))
                    v_load = st.text_input(fmt_label("Sanction Load", "sanction_load"), value=result.get("sanction_load", ""))
                    v_unit = st.text_input(fmt_label("Sanction Load Unit", "sanction_load_unit"), value=result.get("sanction_load_unit", ""))
                    v_ucons = st.text_input(fmt_label("Unit Consumed", "unit_consumed"), value=result.get("unit_consumed", ""))
                    v_rate = st.text_input(fmt_label("Rate Per Unit", "rate_per_unit"), value=result.get("rate_per_unit", ""))
                    
                # Pack modified payload for download data syncing
                validated_payload = {
                    "name": v_name, "consumer_number": v_cons, "total_bill_amount": v_amt,
                    "bill_date": v_date, "arrears": v_arr, "address": v_addr, "pincode": v_pin,
                    "sanction_load": v_load, "sanction_load_unit": v_unit, "unit_consumed": v_ucons,
                    "rate_per_unit": v_rate,
                    "confidence_scores": conf_scores,
                    "overall_confidence": overall_conf
                }
                
                st.download_button(
                    label="Download Verified Clean JSON",
                    data=json.dumps(validated_payload, indent=2),
                    file_name="bill_record.json",
                    mime="application/json"
                )
                
                # CSV Download
                # Flattening confidence_scores to a JSON string to prevent Pandas DataFrame errors
                csv_payload = validated_payload.copy()
                csv_payload["confidence_scores"] = json.dumps(conf_scores)
                df = pd.DataFrame([csv_payload])
                csv = df.to_csv(index=False)
                st.download_button(
                    "Download CSV",
                    csv,
                    "bill.csv",
                    "text/csv"
                )
