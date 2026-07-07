import os
import json
import glob
import time
import pandas as pd
from tqdm import tqdm
from datetime import datetime
from utils.ocr_engine4 import pipeline_extract
from groq import RateLimitError
import fitz

# =========================
# CONFIG
# =========================
INPUT_FOLDER = "./300 bills"
OUTPUT_FOLDER = "./batch_results5_300"
MAX_FILES = 300
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Rate limit handling config
MAX_RETRIES = 5
BASE_WAIT_TIME = 10  # seconds

# =========================
# MOCK STREAMLIT FILE
# =========================
class MockUploadedFile:
    def __init__(self, filepath):
        self.filepath = filepath
        self.name = os.path.basename(filepath)
    
    def read(self):
        with open(self.filepath, "rb") as f:
            return f.read()

# =========================
# FIND FILES
# =========================
files = [f for f in os.listdir(INPUT_FOLDER) if f.lower().endswith((".pdf", ".png", ".jpg", ".jpeg"))][:MAX_FILES]
print(f"\nFound {len(files)} files to process (max: {MAX_FILES})\n")

results = []
failed_files = []
rate_limit_hits = 0

# =========================
# PROCESS FILES WITH RATE LIMIT HANDLING
# =========================
for file_idx, filename in enumerate(tqdm(files, desc="Processing Documents")):
    filepath = os.path.join(INPUT_FOLDER, filename)
    
    attempt = 0
    success = False
    
    while attempt < MAX_RETRIES and not success:
        try:
            print(f"\n[{file_idx + 1}/{len(files)}] Processing: {filename}")
            
            uploaded_file = MockUploadedFile(filepath)
            output = pipeline_extract(uploaded_file)
            
            if not isinstance(output, dict):
                output = {"error": "Invalid output returned"}
            
            # Remove raw OCR dump for clean JSON
            output.pop("_raw_text", None)
            
            # Final schema
            final_output = {
                "file_name": filename,
                "name": output.get("name"),
                "address": output.get("address"),
                "pincode": output.get("pincode"),
                "sanction_load": output.get("sanction_load"),
                "sanction_load_unit": output.get("sanction_load_unit"),
                "total_bill_amount": output.get("total_bill_amount"),
                "bill_date": output.get("bill_date"),
                "unit_consumed": output.get("unit_consumed"),
                "arrears": output.get("arrears"),
                "consumer_number": output.get("consumer_number"),
                "rate_per_unit": output.get("rate_per_unit")
            }
            
            # =========================
            # SAVE INDIVIDUAL JSON
            # =========================
            json_path = os.path.join(OUTPUT_FOLDER, f"{os.path.splitext(filename)[0]}.json")
            
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(final_output, f, indent=2, ensure_ascii=False)
            
            results.append(final_output)
            print(f"✓ Saved JSON: {json_path}")
            success = True
            
        except RateLimitError as e:
            rate_limit_hits += 1
            wait_time = (2 ** attempt) * BASE_WAIT_TIME  # Exponential backoff: 10s, 20s, 40s, 80s, 160s
            print(f"\n⚠️  Rate limit hit! (Attempt {attempt + 1}/{MAX_RETRIES})")
            print(f"⏸️  Pausing for {wait_time} seconds to allow tokens to restore...")
            time.sleep(wait_time)
            attempt += 1
            
        except Exception as e:
            print(f"✗ Failed: {filename}")
            print(f"Reason: {str(e)}")
            
            results.append({
                "file_name": filename,
                "name": None,
                "address": None,
                "pincode": None,
                "sanction_load": None,
                "sanction_load_unit": None,
                "total_bill_amount": None,
                "bill_date": None,
                "unit_consumed": None,
                "arrears": None,
                "consumer_number": None,
                "rate_per_unit": None,
                "error": str(e)
            })
            failed_files.append(filename)
            success = True  # Don't retry on non-rate-limit errors
            break
    
    if not success:
        print(f"✗ Max retries exceeded for {filename}. Skipping...")
        failed_files.append(filename)
        results.append({
            "file_name": filename,
            "name": None,
            "address": None,
            "pincode": None,
            "sanction_load": None,
            "sanction_load_unit": None,
            "total_bill_amount": None,
            "bill_date": None,
            "unit_consumed": None,
            "arrears": None,
            "consumer_number": None,
            "rate_per_unit": None,
            "error": "Max retries exceeded due to rate limiting"
        })

# =========================
# SAVE MASTER CSV
# =========================
summary_csv = os.path.join(OUTPUT_FOLDER, "summary.csv")
pd.DataFrame(results).to_csv(summary_csv, index=False)

# =========================
# SAVE FAILED FILES LIST
# =========================
if failed_files:
    failed_txt = os.path.join(OUTPUT_FOLDER, "failed_files.txt")
    with open(failed_txt, "w") as f:
        for filename in failed_files:
            f.write(f"{filename}\n")

# =========================
# VALIDATION & STATISTICS
# =========================
json_files = glob.glob(os.path.join(OUTPUT_FOLDER, "*.json"))

# Calculate accuracy metrics
successful_extractions = sum(1 for r in results if r.get("consumer_number") or r.get("total_bill_amount"))
complete_records = sum(1 for r in results if all([
    r.get("consumer_number"),
    r.get("total_bill_amount"),
    r.get("unit_consumed"),
    r.get("bill_date")
]))

print("\n" + "=" * 60)
print("BATCH PROCESSING COMPLETE")
print("=" * 60)
print(f"Input Files           : {len(files)}")
print(f"JSON Files Generated  : {len(json_files)}")
print(f"CSV Rows              : {len(results)}")
print(f"Rate Limit Hits       : {rate_limit_hits}")
print(f"Failed Files          : {len(failed_files)}")
print("-" * 60)
print(f"Successful Extractions: {successful_extractions}/{len(results)} ({successful_extractions/len(results)*100:.1f}%)")
print(f"Complete Records      : {complete_records}/{len(results)} ({complete_records/len(results)*100:.1f}%)")
print("-" * 60)
print(f"Summary CSV           : {summary_csv}")
if failed_files:
    print(f"Failed Files List     : {failed_txt}")
print("=" * 60)

# =========================
# FIELD COMPLETENESS ANALYSIS
# =========================
print("\nFIELD COMPLETENESS:")
print("-" * 60)
fields = ["consumer_number", "name", "address", "total_bill_amount", 
          "unit_consumed", "bill_date", "rate_per_unit", "arrears"]
for field in fields:
    count = sum(1 for r in results if r.get(field) is not None)
    percentage = (count / len(results)) * 100
    print(f"{field:25}: {count:3}/{len(results)} ({percentage:5.1f}%)")
print("=" * 60)