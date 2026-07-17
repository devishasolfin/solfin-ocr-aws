import os
import json
import re
import fitz
import boto3
from groq import Groq
from pydantic import BaseModel, Field
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

# Initialize AWS Client for Textract
textract_client = boto3.client(
    "textract",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION", "ap-south-1")
)

# Initialize Groq Cloud Client for Llama 3
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Define strict target extraction schema using Pydantic
class UtilityBillSchema(BaseModel):
    name: Optional[str] = Field(default=None, description="Full name of the customer/consumer")
    address: Optional[str] = Field(default=None, description="Complete billing address details")
    pincode: Optional[str] = Field(default=None, description="6-digit postal code/pincode found in address block")
    sanction_load: Optional[str] = Field(default=None, description="Sanctioned load numerical value")
    sanction_load_unit: Optional[str] = Field(default=None, description="Unit for sanction load, e.g., KW, KVA, HP")
    total_bill_amount: Optional[str] = Field(default=None, description="Total net payable amount or current invoice amount")
    bill_date: Optional[str] = Field(default=None, description="Date of bill issuance or invoice creation")
    unit_consumed: Optional[str] = Field(default=None, description="Total utility units consumed during billing timeline")
    arrears: Optional[str] = Field(default=None, description="Previous outstanding dues or arrears balances if any")
    consumer_number: Optional[str] = Field(default=None, description="Unique consumer ID, account number, or CA number")
    rate_per_unit: Optional[str] = Field(
        default=None,
        description="Tariff calculation rate applied per unit consumed. If not explicitly mentioned in the text, calculate it as total_bill_amount / unit_consumed."
    )

def get_textract_structured_text(image_bytes: bytes) -> str:
    """Uses Textract analyze_document with FORMS and TABLES to extract structured context and native confidence scores."""
    response = textract_client.analyze_document(
        Document={"Bytes": image_bytes},
        FeatureTypes=["TABLES", "FORMS"]
    )
    blocks = response.get("Blocks", [])
    block_map = {b["Id"]: b for b in blocks}

    # Helper to extract text and average confidence from child WORD blocks
    def get_text_and_conf(block_id):
        block = block_map.get(block_id)
        if not block:
            return "", 0.0
        text = []
        confs = []
        for rel in block.get("Relationships", []):
            if rel["Type"] == "CHILD":
                for child_id in rel.get("Ids", []):
                    child = block_map.get(child_id)
                    if child and child["BlockType"] == "WORD":
                        text.append(child["Text"])
                        confs.append(child.get("Confidence", 100.0)) # Native Textract confidence (0-100)
        avg_conf = sum(confs) / len(confs) if confs else 0.0
        return " ".join(text), avg_conf / 100.0 # Normalize to 0.0 - 1.0

    forms = []
    tables = []
    lines = []

    for block in blocks:
        # 1. Extract Key-Value Pairs (Forms) with Confidence
        if block["BlockType"] == "KEY_VALUE_SET":
            if "KEY" in block.get("EntityTypes", []):
                key, _ = get_text_and_conf(block["Id"])
                val = ""
                val_conf = 0.0
                for rel in block.get("Relationships", []):
                    if rel["Type"] == "VALUE":
                        for val_id in rel.get("Ids", []):
                            if val_id in block_map:
                                val, val_conf = get_text_and_conf(val_id)
                if key:
                    # Inject the real Textract confidence score into the prompt context
                    forms.append(f"{key}: {val} (Textract Confidence: {val_conf:.2f})")
        
        # 2. Extract Tables (Reconstruct Rows and Columns)
        elif block["BlockType"] == "TABLE":
            rows = {}
            for rel in block.get("Relationships", []):
                if rel["Type"] == "CHILD":
                    for cell_id in rel.get("Ids", []):
                        cell = block_map.get(cell_id)
                        if cell and cell["BlockType"] == "CELL":
                            r = cell.get("RowIndex", 1)
                            c = cell.get("ColumnIndex", 1)
                            text, _ = get_text_and_conf(cell_id)
                            rows.setdefault(r, {})[c] = text
            if rows:
                table_str = []
                for r in sorted(rows.keys()):
                    cols = rows[r]
                    row_str = " | ".join(cols.get(c, "") for c in sorted(cols.keys()))
                    table_str.append(row_str)
                tables.append("\n".join(table_str))
        
        # 3. Fallback Raw Lines
        elif block["BlockType"] == "LINE":
            lines.append(block["Text"])

    # Combine into a highly structured prompt format
    out = []
    if forms:
        out.append("[FORMS]\n" + "\n".join(forms))
    if tables:
        out.append("[TABLES]\n" + "\n".join(tables))
    if lines:
        out.append("[RAW_LINES]\n" + "\n".join(lines))
        
    return "\n\n".join(out)

def process_text_with_llama(raw_ocr_text: str) -> dict:
    """Uses Groq's Llama 3 endpoint with structured JSON mode to map raw text to schema and generate real confidence scores."""
    prompt = f"""You are a structural document parsing engine. Analyze the following structured OCR output (containing extracted Forms, Tables, and Raw Lines) taken from a utility bill and populate the requested schema accurately.

Strict Rules:
1. Isolate alphanumeric strings precisely (especially dates, consumer numbers, amounts).
2. If a specific data point is missing or not mentioned in the text, map its field value to null.
3. Do not assume or extrapolate values, EXCEPT for 'rate_per_unit': if it is not explicitly mentioned in the document, you MUST calculate it by dividing the 'total_bill_amount' by the 'unit_consumed'.
4. You MUST output a "confidence_scores" dictionary alongside the "data". 
   - For fields extracted from [FORMS], use the exact "Textract Confidence" value provided in the text.
   - For fields extracted from [TABLES], assign a confidence of 0.85.
   - For fields extracted from [RAW_LINES] (without an explicit confidence), assign 0.60.
   - For calculated fields (like rate_per_unit), assign 0.80.
   - For missing/null fields, assign 0.0.

Output ONLY valid JSON with exactly two top-level keys:
1. "data": The extracted values matching the schema.
2. "confidence_scores": A dictionary mapping each field name to its confidence score (float between 0.0 and 1.0).

Structured Utility Bill Document Text:
{raw_ocr_text}
"""
    chat_completion = groq_client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": f"You are a strict data extractor that outputs ONLY valid JSON objects with 'data' and 'confidence_scores' keys. Schema for 'data': {json.dumps(UtilityBillSchema.model_json_schema())}"
            },
            {
                "role": "user",
                "content": prompt,
            }
        ],
        model="llama-3.3-70b-versatile",
        response_format={"type": "json_object"},
        temperature=0.1
    )

    try:
        response_json = json.loads(chat_completion.choices[0].message.content)
        
        # Handle cases where LLM might just return the flat data instead of nested
        if "data" in response_json and "confidence_scores" in response_json:
            parsed_data = response_json["data"]
            conf_scores = response_json["confidence_scores"]
        else:
            parsed_data = response_json
            conf_scores = {k: (0.6 if v else 0.0) for k, v in parsed_data.items()}

        # Ensure all schema fields have a confidence score
        for field in UtilityBillSchema.model_fields.keys():
            if field not in conf_scores:
                conf_scores[field] = 0.0 if not parsed_data.get(field) else 0.5

        # --- Fallback Calculation for rate_per_unit ---
        if not parsed_data.get("rate_per_unit"):
            def clean_numeric(val):
                if not val: return None
                val = re.sub(r'[^\d.]', '', str(val))
                return float(val) if val else None
            try:
                amt = clean_numeric(parsed_data.get("total_bill_amount"))
                units = clean_numeric(parsed_data.get("unit_consumed"))
                if amt is not None and units and units > 0:
                    calculated_rate = round(amt / units, 2)
                    parsed_data["rate_per_unit"] = str(calculated_rate)
                    conf_scores["rate_per_unit"] = 0.80 # Calculated fields get 0.80
            except Exception:
                pass

        # Calculate Overall Confidence (average of non-null fields)
        valid_scores = [v for k, v in conf_scores.items() if parsed_data.get(k)]
        overall_conf = sum(valid_scores) / len(valid_scores) if valid_scores else 0.0

        # Flatten the result so app6.py can access fields directly (e.g., result.get("name"))
        final_result = parsed_data.copy()
        final_result["confidence_scores"] = conf_scores
        final_result["overall_confidence"] = overall_conf
        
        return final_result

    except (json.JSONDecodeError, IndexError) as e:
        return {"error": "Failed to safely parse Llama data payload.", "details": str(e)}

def pipeline_extract(uploaded_file) -> dict:
    """Pipelines image ingestion, upscales matrices, executes layout OCR, and triggers Llama schema parsing."""
    file_bytes = uploaded_file.read()
    filename = uploaded_file.name.lower()
    combined_raw_text = ""
    
    if filename.endswith(".pdf"):
        pdf = fitz.open(stream=file_bytes, filetype="pdf")
        for page_no in range(len(pdf)):
            page = pdf[page_no]
            # Matrix 3x3 balances high accuracy for Textract Tables/Forms with processing speed
            pix = page.get_pixmap(matrix=fitz.Matrix(3, 3)) 
            img_bytes = pix.tobytes("png")
            combined_raw_text += f"\n--- PAGE {page_no + 1} ---\n{get_textract_structured_text(img_bytes)}"
    else:
        combined_raw_text = get_textract_structured_text(file_bytes)

    parsed_data = process_text_with_llama(combined_raw_text)
    
    # Inject raw text into the response so the UI can display it in a separate column
    if isinstance(parsed_data, dict) and "error" not in parsed_data:
        parsed_data["_raw_text"] = combined_raw_text
        
    return parsed_data