# 🛡️ SafeGuard AI — Next-Gen Cyber Safety & FIR Platform

> AI-powered platform to detect harmful online content, protect children, and generate legally valid FIR reports under Indian law — in seconds.

![SafeGuard AI](https://img.shields.io/badge/version-3.1.0-red?style=flat-square)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square)
![Next.js](https://img.shields.io/badge/Next.js-14-black?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)

---

## 🎯 What It Does

| Feature | Description |
|---|---|
| **Multi-Label AI** | Detects cyberbullying, threats, hate speech, sexual harassment simultaneously |
| **Grooming Detection** | Pattern-based + ML detection of child-targeting behaviour |
| **Explainable AI** | Token-level highlighting shows exactly which words triggered the alert |
| **Multilingual** | Hindi, Bengali, Hinglish, l33tspeak normalization |
| **Legal Mapping** | Auto-maps violations → IT Act 2000, IPC, POCSO Act |
| **FIR Generator** | Court-ready PDF with Cloudinary evidence links, timestamps, legal sections |
| **OCR** | Tesseract extracts text from screenshots and images |
| **Context Analysis** | Escalation detection across full conversation threads |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Next.js Frontend                      │
│  Landing Page · Dashboard · Analytics · FIR Generator   │
└──────────────────────┬──────────────────────────────────┘
                       │ REST API
┌──────────────────────▼──────────────────────────────────┐
│                  FastAPI Backend                         │
│  /analyze-text · /analyze-image · /generate-fir         │
├─────────────────────────────────────────────────────────┤
│   AI Services Layer                                      │
│   ToxicityClassifier · GroomingDetector                  │
│   ContextAnalyzer · MultilingualProcessor                │
├──────────────┬──────────────┬───────────────────────────┤
│   MongoDB    │    Redis     │    Cloudinary              │
│  (analyses)  │  (Celery)    │  (evidence + FIR PDFs)    │
└──────────────┴──────────────┴───────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker & Docker Compose
- MongoDB 7+ (or Atlas URI)
- Redis 7+
- Tesseract OCR (`apt install tesseract-ocr tesseract-ocr-hin tesseract-ocr-ben`)
- Cloudinary account

---

### 1. Clone & Configure

```bash
git clone https://github.com/your-org/safeguard-ai.git
cd safeguard-ai

# Copy and fill in environment variables
cp .env.example .env
```

Fill in `.env`:
```env
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
MONGODB_URI=mongodb://localhost:27017
```

---

### 2. Docker Compose (Recommended)

```bash
# Build and start all services
docker compose up --build

# Services available at:
#   Frontend:  http://localhost:3000
#   Backend:   http://localhost:8000
#   API Docs:  http://localhost:8000/docs
#   Flower:    http://localhost:5555
```

---

### 3. Manual Development Setup

**Backend:**
```bash
cd ai-safety-platform

# Create virtualenv
python -m venv venv
source venv/bin/activate  # macOS/Linux
# Windows PowerShell: .\venv\Scripts\Activate.ps1

# Install dependencies
python -m pip install -r requirements.txt

# Start FastAPI
cd backend
python -m uvicorn main:app --reload --port 8000

# Start Celery worker (separate terminal)
python -m celery -A workers.celery_app worker --loglevel=info
```

**Frontend:**
```bash
cd frontend

# Install dependencies
npm install

# Set environment variable
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# Start dev server
npm run dev
# → http://localhost:3000
```

---

## 📡 API Reference

### `POST /analyze-text`
Analyze raw text for harmful content.

```json
// Request
{ "text": "I know where you live and I'll make you regret this." }

// Response
{
  "id": "uuid",
  "risk_level": "CRITICAL",
  "overall_score": 0.91,
  "labels": {
    "cyberbullying": 0.45,
    "threat": 0.92,
    "hate_speech": 0.1,
    "sexual_harassment": 0.0,
    "grooming": 0.0
  },
  "toxic_tokens": [
    { "token": "know where you live", "score": 0.88, "category": "threat" }
  ],
  "highlighted_text": "<HTML with <mark> tags>",
  "legal_mappings": [
    {
      "law": "Indian Penal Code",
      "section": "IPC Section 503 — Criminal Intimidation",
      "description": "...",
      "severity": "HIGH"
    }
  ],
  "explanation": "The AI flagged this at CRITICAL risk...",
  "language_detected": "en"
}
```

---

### `POST /analyze-image`
Upload an image (multipart/form-data). OCR extracts text, then full analysis runs.

```bash
curl -X POST http://localhost:8000/analyze-image \
  -F "file=@screenshot.png"
```

---

### `POST /analyze-context`
Analyze a full conversation thread.

```json
{
  "messages": [
    { "role": "sender", "text": "Hey, you seem mature for your age." },
    { "role": "receiver", "text": "Thanks, I'm 13." },
    { "role": "sender", "text": "Let's keep this our secret, ok?" }
  ]
}
```

---

### `POST /generate-fir`
Create a FIR record from an analysis.

```json
{ "analysis_id": "uuid-from-analyze" }
// → { "fir_id": "FIR-20241201-AB12CD34" }
```

---

### `POST /finalize-fir`
Generate and upload the court-ready PDF.

```json
{
  "fir_id": "FIR-20241201-AB12CD34",
  "analysis_id": "uuid",
  "complainant_name": "Priya Sharma",
  "complainant_contact": "+91 9876543210",
  "incident_date": "2024-12-01",
  "additional_info": "Harassment started 3 weeks ago.",
  "legal_sections": ["IPC 506", "IT Act 66C"],
  "evidence_urls": ["https://res.cloudinary.com/..."]
}
```

---

### `GET /download-fir/{fir_id}`
Stream the PDF for download.

---

### `GET /analytics`
Returns platform-wide stats.

---

## 🧠 AI Models

| Component | Model / Method |
|---|---|
| Toxic Gate (Stage 1) | `microsoft/mdeberta-v3-base` (optional, high-recall binary gate) |
| Multi-label Core (Stage 2) | `xlm-roberta-large` (optional multi-label head, fused with deterministic rules) |
| Grooming | Specialist grooming detector + behavioral rule patterns |
| Context Escalation (Stage 3) | Optional `Qwen2.5-7B-Instruct` endpoint (JSON-scored, risk-triggered only) |
| Multilingual | `langdetect` + Hinglish/Indic normalization + obfuscation cleanup |
| OCR | PaddleOCR primary (optional), EasyOCR fallback (optional), Tesseract tertiary |
| Explainability | Token-level regex attribution with confidence scores |

---

## ⚖️ Legal Mappings

| Category | Laws Covered |
|---|---|
| Threats | IPC 503, IPC 506, IT Act reference |
| Cyberbullying | IPC 499/500 (Defamation), IT Act 66C/66D |
| Hate Speech | IPC 153A, IPC 295A |
| Sexual Harassment | IPC 354A, IT Act Section 67 |
| Grooming / CSAM | POCSO 11, POCSO 13, IT Act 67B |

---

## 📁 Project Structure

```
ai-safety-platform/
│
├── backend/
│   ├── main.py                    # FastAPI app + startup
│   ├── config/
│   │   ├── settings.py            # Pydantic settings (env vars)
│   │   └── database.py            # Motor async MongoDB
│   ├── routes/
│   │   ├── analysis.py            # /analyze-* endpoints
│   │   ├── fir.py                 # /generate-fir, /download-fir
│   │   └── analytics.py           # /analytics
│   ├── services/
│   │   ├── analysis_service.py    # AI pipeline orchestrator
│   │   ├── fir_service.py         # ReportLab PDF generator
│   │   ├── cloudinary_service.py  # Cloudinary uploads
│   │   └── analytics_service.py   # Stats aggregation
│   ├── models/
│   │   └── schemas.py             # Pydantic request/response models
│   ├── utils/
│   │   ├── legal_mapper.py        # Category → Indian law mapping
│   │   ├── risk_engine.py         # Weighted risk scoring
│   │   ├── explainability.py      # Token highlighting + HTML
│   │   └── ocr.py                 # Tesseract wrapper
│   └── workers/
│       ├── celery_app.py          # Celery configuration
│       └── tasks.py               # Async task definitions
│
├── ai_services/
│   ├── toxicity.py                # HuggingFace + rule-based classifier
│   ├── grooming_detection.py      # Child-targeting pattern detector
│   ├── context_analysis.py        # Conversation escalation analysis
│   └── multilingual_processing.py # Language detect + normalization
│
├── frontend/
│   ├── app/
│   │   ├── page.tsx               # Landing page
│   │   ├── layout.tsx             # Root layout + fonts
│   │   ├── globals.css            # Design tokens + utilities
│   │   ├── dashboard/page.tsx     # Analysis dashboard
│   │   └── analytics/page.tsx     # Analytics dashboard
│   ├── components/
│   │   ├── Navbar.tsx
│   │   ├── landing/
│   │   │   ├── Hero.tsx           # Animated hero + typing effect
│   │   │   ├── Features.tsx       # Feature cards
│   │   │   ├── HowItWorks.tsx     # Step-by-step flow
│   │   │   ├── AIDemo.tsx         # Interactive demo panel
│   │   │   ├── Testimonials.tsx
│   │   │   ├── CTASection.tsx
│   │   │   └── Footer.tsx
│   │   └── dashboard/
│   │       ├── TextAnalyzer.tsx
│   │       ├── ImageAnalyzer.tsx
│   │       ├── ContextAnalyzer.tsx
│   │       ├── ResultsPanel.tsx
│   │       └── FIRModal.tsx
│   ├── services/api.ts            # Axios API client
│   └── types/index.ts             # TypeScript interfaces
│
├── requirements.txt
├── docker-compose.yml
├── Dockerfile.backend
├── frontend/Dockerfile.frontend
├── .env.example
└── README.md
```

---

## 🛠️ Configuration

### Swap AI Model

To use a fine-tuned Indian-language model:

```env
HF_MODEL_NAME=Hate-speech-CNERG/dehatebert-mono-hindi
```

Or a multilingual model:
```env
HF_MODEL_NAME=citizenlab/toxicity-classifier-multilingual
```

### GPU Acceleration

```env
HF_DEVICE=cuda
```

Ensure PyTorch CUDA is installed:
```bash
pip install torch --index-url https://download.pytorch.org/whl/cu121
```

---

## 🔒 Security Notes

- All uploads go to Cloudinary; no files stored locally in production
- MongoDB Atlas with TLS recommended for production
- Use Redis with AUTH in production
- Set `DEBUG=false` and restrict `ALLOWED_ORIGINS` in production
- Run Tesseract as non-root user (enforced in Dockerfile)

---

## 📄 License

MIT — see `LICENSE` for details.

Built with ❤️ in India · SafeGuard AI v3.1.0
#
