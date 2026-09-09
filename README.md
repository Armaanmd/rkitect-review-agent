# rkitect Review Agent

Agentic architectural review API. Ingest a design brief, parse it deterministically, run five domain specialist checks, and synthesize actionable recommendations with a human-approval gate.

## Features

- `POST /v1/reviews` - full pipeline: brief parse → 5 specialists → synthesizer → persisted `ReviewResponse`
- `GET /v1/reviews/{run_id}` - retrieve a completed review
- `POST /v1/reviews/{run_id}/decisions` - accept or reject a recommendation
- `GET /health` - liveness check
- Deterministic rule-based parsing (no external LLM/API dependency)
- High-severity findings automatically gated for human approval

## Local Setup

Requires Python 3.10+.

```powershell
# create and activate a virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# install dependencies
python -m pip install fastapi uvicorn

# install test dependencies
python -m pip install pytest httpx httpx2

# run the test suite
python -m pytest tests/ -v
```

## Run the API

```powershell
uvicorn app.main:app --reload
```

Swagger UI: http://127.0.0.1:8000/docs

## Ready-to-Run Request

Create a review with the standard test brief (92 sq m, 8-seat dining table):

```bash
curl -X POST http://127.0.0.1:8000/v1/reviews \
  -H "Content-Type: application/json" \
  -d "{\"brief\": \"2 bedroom apartment, 92 sq m. Bedroom 1, Bedroom 2 / Study, Kitchen, Living room. Need to work from home and host parents. Prefer open feel, visual connection, and privacy. 8-seat dining table wanted. Maximize storage while keeping wide circulation.\"}"
```

## Architecture

```mermaid
flowchart LR
    Client[Client] -->|POST /v1/reviews| API[FastAPI API]
    API --> Parser[Brief Parser]
    Parser --> S1[Clearances Specialist]
    Parser --> S2[Daylight Specialist]
    Parser --> S3[Privacy Specialist]
    Parser --> S4[Circulation Specialist]
    Parser --> S5[Adjacency Specialist]
    S1 --> Findings[Findings Pool]
    S2 --> Findings
    S3 --> Findings
    S4 --> Findings
    S5 --> Findings
    Findings --> Synth[Synthesizer]
    Synth -->|recommendations| Queue[Approval Queue]
    Synth -->|contains flagged recs| Human[Human Approval]
    Queue --> Client
    Human -->|decision: accept / reject| API

    classDef process fill:#eef,stroke:#338,stroke-width:1px;
    classDef agent fill:#efe,stroke:#383,stroke-width:1px;
    class API,Parser,Synth process;
    class S1,S2,S3,S4,S5 agent;
```