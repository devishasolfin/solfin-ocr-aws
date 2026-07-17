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
│
├── outputs/
│
├── samples/
│
└── screenshots/
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

The pipeline is modular and can be extended to support additional document types without major architectural changes.

GitHub: https://github.com/devishasolfin

LinkedIn: https://www.linkedin.com/in/devishabhargava/
