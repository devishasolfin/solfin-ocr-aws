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

def extract_raw_text_via_textract(image_bytes: bytes) -> str:
    """Uses basic Textract OCR lines to preserve document raw context arrays."""
    response = textract_client.detect_document_text(Document={"Bytes": image_bytes})
    lines = [block["Text"] for block in response.get("Blocks", []) if block["BlockType"] == "LINE"]
    return "\n".join(lines)

def process_text_with_llama(raw_ocr_text: str) -> dict:
    """Uses Groq's Llama 3 endpoint with structured JSON mode to map raw text to schema."""
    prompt = f"""You are a structural document parsing engine. Analyze the following unmapped OCR lines taken from a utility bill and populate the requested schema accurately.
Strict Rules:
1. Isolate alphanumeric strings precisely (especially dates, consumer numbers, amounts).
2. If a specific data point is missing or not mentioned in the text, map its field value to null.
3. Do not assume or extrapolate values, EXCEPT for 'rate_per_unit': if it is not explicitly mentioned in the document, you MUST calculate it by dividing the 'total_bill_amount' by the 'unit_consumed'.
4. Output ONLY valid JSON.

Raw Utility Bill Document Text:
{raw_ocr_text}
"""
    chat_completion = groq_client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": f"You are a strict data extractor that outputs ONLY valid JSON objects matching this JSON Schema: {json.dumps(UtilityBillSchema.model_json_schema())}"
            },
            {
                "role": "user",
                "content": prompt,
            }
        ],
        model="llama-3.1-8b-instant",
        response_format={"type": "json_object"},
        temperature=0.1
    )

    try:
        parsed_data = json.loads(chat_completion.choices[0].message.content)
        
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
            except Exception:
                pass
                
        return parsed_data
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
            pix = page.get_pixmap(matrix=fitz.Matrix(4, 4))
            img_bytes = pix.tobytes("png")
            combined_raw_text += f"\n{extract_raw_text_via_textract(img_bytes)}"
    else:
        combined_raw_text = extract_raw_text_via_textract(file_bytes)
        
    parsed_data = process_text_with_llama(combined_raw_text)
    
    # Inject raw text into the response so the UI can display it in a separate column
    if isinstance(parsed_data, dict) and "error" not in parsed_data:
        parsed_data["_raw_text"] = combined_raw_text
        
    return parsed_data