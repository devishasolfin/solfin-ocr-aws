# Solfin OCR AWS

An Intelligent Document Processing (IDP) pipeline for extracting structured information from electricity bills using **Amazon Textract**, **Large Language Models (Llama 3 via Groq)**, and rule-based validation.

The project is designed to automate data extraction from utility bills of varying layouts and convert unstructured OCR output into validated JSON suitable for downstream financial and verification workflows.

---

## Overview

Electricity bills issued by different DISCOMs vary significantly in layout, terminology, language, and formatting. Traditional OCR systems can extract text but often struggle to reliably identify business-critical fields.

This project combines:

- Amazon Textract for OCR
- Llama 3 for semantic understanding
- Rule-based post-processing
- Mathematical validation
- Structured JSON generation

to build an end-to-end intelligent extraction pipeline.

---

## Features

- PDF and image support
- Amazon Textract OCR
- Automatic multi-page PDF processing
- Structured JSON extraction
- LLM-powered document understanding
- Validation and cross-checking
- Derived field calculation
- Streamlit-based interface
- Batch document processing
- Extensible extraction schema

---

## Extraction Pipeline

```text
                Input Document
             (PDF / PNG / JPG)
                     │
                     ▼
          PDF Rendering (PyMuPDF)
                     │
                     ▼
        Amazon Textract OCR Engine
                     │
                     ▼
         Raw OCR Text Aggregation
                     │
                     ▼
     Prompt-based Llama 3 Extraction
             (Groq Inference)
                     │
                     ▼
      Rule-based Validation Engine
                     │
                     ▼
        Business Logic Corrections
                     │
                     ▼
            Structured JSON Output
```

---

# Supported Document Types

- Electricity Bills
- Utility Bills
- Consumer Bills
- Single-page Documents
- Multi-page PDFs

---

# Extracted Fields

The system extracts the following information:

| Field | Description |
|---------|-------------|
| discom | Electricity provider |
| consumer_number | Consumer / CA / Account Number |
| name | Consumer Name |
| address | Consumer Address |
| pincode | Postal Code |
| sanction_load | Connected Load |
| sanction_load_unit | KW / HP / KVA |
| total_bill_amount | Total Payable Amount |
| bill_amount | Current Bill Amount |
| arrears | Outstanding Amount |
| overdue_months_count | Estimated overdue duration |
| bill_date | Bill Generation Date |
| unit_consumed | Energy Consumption |
| rate_per_unit | Tariff |
| combined_bill | Multi-month bill detection |
| verification_check | Validation results |
| note | Processing remarks |

---

# Validation Engine

The pipeline performs automatic validation before returning results.

## Mathematical Validation

Checks include:

- Bill Amount + Arrears ≈ Total Amount
- Rate × Units ≈ Bill Amount

---

## Field Validation

- Date formatting
- Numeric validation
- Pincode verification
- Missing mandatory fields
- OCR quality assessment

---

## Business Rules

Examples include:

- Estimate overdue months
- Calculate rate per unit
- Detect combined bills
- Reject non-electricity documents

---

# Technology Stack

| Component | Technology |
|------------|------------|
| Language | Python 3.10+ |
| OCR | Amazon Textract |
| LLM | Llama 3.1 8B versatile (Groq) |
| PDF Rendering | PyMuPDF |
| Validation | Python |
| API | Groq API |
| UI | Streamlit |
| Cloud | AWS |

---

# Project Structure

```
solfin-ocr-aws/
│
├── app.py
├── batch_testing.py
├── ocr_engine.py
├── requirements.txt
├── .env
├── README.md
│
├── outputs/
│
├── samples/
└──
```

---

# Installation

Clone the repository

```bash
git clone https://github.com/devishasolfin/solfin-ocr-aws.git

cd solfin-ocr-aws
```

Install dependencies

```bash
pip install -r requirements.txt
```

---

# AWS Configuration

Create a `.env` file

```env
AWS_ACCESS_KEY_ID=xxxxxxxxxxxxxxxx
AWS_SECRET_ACCESS_KEY=xxxxxxxxxxxxxxxx
AWS_REGION=ap-south-1

GROQ_API_KEY=xxxxxxxxxxxxxxxx
```

---

# Running the Application

Start Streamlit

```bash
streamlit run app.py
```

The application will be available at

```
http://localhost:8501
```

---

# Batch Processing

For evaluating multiple documents

```bash
python batch_testing5.py
```

Outputs can be exported as

- JSON
- CSV

making it suitable for benchmarking against manually reviewed datasets.

---

# Example Output

```json
{
  "file_name": aojaooajdaodaopdapd.pdf,
  "consumer_number": "211584042333",
  "name": "John Doe",
  "address": "Ahmedabad, Gujarat",
  "pincode": "132455",
  "bill_date": "21/11/2025",
  "sanction_load": 1,
  "sanction_load_unit": kW,
  "unit_consumed": 225,
  "bill_amount": 1420,
  "arrears": 200,
  "total_bill_amount": 1620,
  "rate_per_unit": 6.31
}
```

---

# Current Limitations

The current implementation uses Amazon Textract's `DetectDocumentText` API.

Performance is strongest on English-language documents but may degrade for certain Indic scripts such as:

- Gujarati
- Bengali
- Tamil
- Telugu
- Malayalam
- Kannada

Future versions will integrate multilingual OCR and layout-aware document understanding to improve extraction accuracy for regional electricity bills.

---

Here is a complete, well-structured `README.md` file designed to help your team seamlessly integrate this Python OCR engine with a Java (Spring Boot) backend and a JavaScript frontend.

***

# Utility Bill OCR & Extraction Engine

This project provides a robust Python-based pipeline for extracting structured data from utility bills (PDFs/Images). It uses **AWS Textract** for high-fidelity OCR and **Groq (Llama 3)** for semantic data extraction, backed by deterministic regex fallbacks for critical fields like Sanctioned Load and Pincode.

## 🏗️ Architecture Flow

```text
[ Frontend (JS) ]  --->  [ Java Backend (Spring Boot) ]  --->  [ Python API (FastAPI) ]
   (Upload File)          (Process & Route)                     (Textract + Llama 3)
```

---

## ⚙️ 1. Python API Setup

The provided `ocr_engine4.py` is a processing module. To integrate it with Java/JS, you must expose it as a REST API. We recommend using **FastAPI**.

### Prerequisites
```bash
pip install fastapi uvicorn python-multipart boto3 groq pydantic PyMuPDF python-dotenv
```

### API Wrapper (`main.py`)
Create a `main.py` file to wrap the engine:
```python
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from ocr_engine4 import pipeline_extract
import uvicorn

app = FastAPI(title="Utility Bill OCR API")

# Allow CORS for Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Restrict to your frontend URL in production
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/extract-bill")
async def extract_bill(file: UploadFile = File(...)):
    try:
        # Pass the uploaded file directly to the pipeline
        result = pipeline_extract(file)
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["details"])
            
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Environment Variables (`.env`)
```env
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
AWS_REGION=ap-south-1
GROQ_API_KEY=your_groq_api_key
```

---

## ☕ 2. Java Backend Integration (Spring Boot)

The Java backend acts as the gateway. It receives the file from the frontend and forwards it to the Python API.

### A. Data Transfer Objects (DTOs)
Create these POJOs to map the JSON response from Python. We use `@JsonProperty` to handle the `snake_case` keys.

```java
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;

@Data
public class UtilityBillResponse {
    private String name;
    private String address;
    private String pincode;
    
    @JsonProperty("sanction_load")
    private String sanctionLoad;
    
    @JsonProperty("sanction_load_unit")
    private String sanctionLoadUnit;
    
    @JsonProperty("total_bill_amount")
    private String totalBillAmount;
    
    @JsonProperty("bill_date")
    private String billDate;
    
    @JsonProperty("unit_consumed")
    private String unitConsumed;
    
    private String arrears;
    
    @JsonProperty("consumer_number")
    private String consumerNumber;
    
    @JsonProperty("rate_per_unit")
    private String ratePerUnit;
    
    @JsonProperty("_raw_text")
    private String rawOcrText; // Injected by Python for UI debugging
}
```

### B. Service Layer (Calling Python)
Use `RestTemplate` to send the `MultipartFile` to the Python API.

```java
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.http.*;
import org.springframework.web.multipart.MultipartFile;

@Service
public class BillExtractionService {

    private final RestTemplate restTemplate = new RestTemplate();
    private final String PYTHON_API_URL = "http://localhost:8000/api/extract-bill";

    public UtilityBillResponse extractBill(MultipartFile file) throws Exception {
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.MULTIPART_FORM_DATA);

        // Convert MultipartFile to Resource
        MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
        body.add("file", file.getResource());

        HttpEntity<MultiValueMap<String, Object>> requestEntity = new HttpEntity<>(body, headers);

        // Call Python API
        ResponseEntity<UtilityBillResponse> response = restTemplate.exchange(
                PYTHON_API_URL,
                HttpMethod.POST,
                requestEntity,
                UtilityBillResponse.class
        );

        return response.getBody();
    }
}
```

---

## 🌐 3. JavaScript Frontend Integration

The frontend needs to capture the file and send it to the Java backend using `FormData`.

### HTML Structure
```html
<input type="file" id="billFile" accept=".pdf,.png,.jpg,.jpeg" />
<button onclick="uploadBill()">Extract Bill Data</button>
<pre id="result"></pre>
```

### JavaScript (Fetch API)
```javascript
async function uploadBill() {
    const fileInput = document.getElementById('billFile');
    const file = fileInput.files[0];
    
    if (!file) {
        alert("Please select a file first!");
        return;
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
        // Send to Java Backend
        const response = await fetch('http://localhost:8080/api/bills/extract', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        
        // Display the extracted data
        document.getElementById('result').textContent = JSON.stringify(data, null, 2);
        
        // Example of accessing specific fields (camelCase in JS)
        console.log("Consumer Name:", data.name);
        console.log("Sanctioned Load:", data.sanctionLoad, data.sanctionLoadUnit);
        console.log("Pincode:", data.pincode);

    } catch (error) {
        console.error("Extraction failed:", error);
        document.getElementById('result').textContent = "Error extracting bill data.";
    }
}
```

---

## 🛠️ Troubleshooting & Tips

1. **Missing Sanctioned Load / Pincode?**
   - The Python script uses strict Regex fallbacks. If the OCR text is too corrupted, check the `_raw_text` field in the JSON response to see what Textract actually read.
2. **Java JSON Parsing Errors?**
   - Ensure your Java project has Jackson dependencies. If you prefer not to use `@JsonProperty` on every field, you can configure Jackson globally in `application.yml`:
     ```yaml
     spring:
       jackson:
         property-naming-strategy: SNAKE_CASE
     ```
3. **Python Timeout Errors?**
   - LLM API calls and PDF rendering can take 10-20 seconds. Ensure your Java `RestTemplate` and Frontend `fetch` timeouts are configured to handle long-running requests (e.g., set timeout to 60 seconds).


# Future Improvements

- Textract Forms & Tables API
- Layout-aware extraction
- Multilingual OCR
- Surya OCR integration
- PaddleOCR integration
- IndicTrans2 translation
- Confidence-based extraction
- Region-wise DISCOM templates
- Automatic language detection
- Rule-based field extraction
- Confidence scoring
- Human-in-the-loop review
- REST API deployment
- Docker support
- Kubernetes deployment

---

# Applications

- Loan underwriting
- KYC verification
- Utility bill verification
- Address proof extraction
- Customer onboarding
- Intelligent Document Processing
- Financial document automation

---

# Performance Considerations

The current architecture prioritizes:

- Low latency
- Deterministic extraction
- JSON consistency
- Validation before output
- Extensible extraction schema
