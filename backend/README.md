# BIS Standards Recommendation Engine — Backend

FastAPI backend powering the AI-driven mapping of procurement requirements to
Bureau of Indian Standards (BIS) codes, QCO alerts, and compliance clauses.

## Architecture

```
backend/
├── main.py              # FastAPI app: /recommend + /audit-pdf endpoints
├── database/
│   ├── __init__.py      # SQLAlchemy engine + session factory
│   └── models.py        # Schemas: Standards, QCOAlerts, SimplifiedProcedure754
├── pipeline/
│   ├── __init__.py
│   └── rag_engine.py    # LangChain + BGE-M3 + Qdrant + LLM synthesis
└── requirements.txt
```

## Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Start Qdrant (Docker)
docker run -p 6333:6333 qdrant/qdrant

# Run the API
uvicorn main:app --reload --port 8000
```

## Endpoints

| Method | Path                  | Purpose                                    |
|--------|-----------------------|--------------------------------------------|
| POST   | `/api/v1/recommend`   | Semantic search → recommendations + clause |
| POST   | `/api/v1/audit-pdf`   | Extract & flag IS codes from tender PDFs   |
| GET    | `/api/v1/health`      | Health check                               |

## Key Design Decisions

- **BGE-M3 embeddings** provide both dense and sparse vectors natively, enabling
  true hybrid search in Qdrant without a separate BM25 pipeline.
- **SQLAlchemy models** track QCO mandatory flags, CRS applicability, and the
  754-Product Simplified Procedure list for 30-day fast-track licensing.
- **LangChain legal prompt** synthesizes retrieved standards + BIS Act text into
  ready-to-insert tender compliance clauses. Falls back to template generation
  if no local LLM is loaded.
- **PyMuPDF** extracts text from legacy tender PDFs for reverse auditing.
