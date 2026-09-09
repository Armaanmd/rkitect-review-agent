# Development Log

## Project Overview

**rkitect Review Agent** - An agentic architectural review API that ingests a design brief, parses it deterministically, runs domain-specialist checks (clearances, daylight, privacy, circulation, adjacency), synthesizes findings into actionable recommendations with human-approval gates, and exposes REST endpoints for review creation, retrieval, and decision recording.

**Stack:** Python 3.11, FastAPI, Pydantic v2, pytest, in-memory state.

## Milestones

### 1. Data Contracts (`app/schemas.py`)
Defined Pydantic v2 models:

- `ReviewRequest` - `brief`, optional `constraints`, optional `plan_data` (dict | str)
- `SpecialistFinding` - `category` (enum-like regex), `severity`, `confidence`, `finding`, `evidence`, `assumptions`
- `Recommendation` - `id`, `title`, `description`, `impact`, `requires_human_approval`, `decision_status` (default `'pending'`)
- `ReviewResponse` - `run_id`, `status`, `structured_brief`, `missing_information`, `contradictions`, findings, recommendations
- `DecisionRequest` - `recommendation_id`, `action` restricted to `accept` / `reject`

Constraints are enforced with `Field(..., pattern=...)` rather than `Literal` to keep coercion simple and serialization clean.

### 2. API Shell (`app/main.py`)
FastAPI app with health, review creation, review retrieval, and decision routes. Initially placeholder-only, later wired to the full agent pipeline.

### 3. In-Memory State (`app/state.py`)
`reviews_db: dict[str, ReviewResponse]` with `save_review()` / `get_review()` helpers.

### 4. Deterministic Brief Parser (`app/agent/brief_parser.py`)
Rule-based keyword/regex parsing with no external API dependency:

- Extracts spaces, requirements, preferences
- Flags missing critical data (orientation, drawing scale, sill heights / obstructions, floor area, budget)
- Detects design tensions (e.g., 8-seat dining in ~92 sq m; storage vs. circulation)
- Generates clarification questions

### 5. Specialist Agents (`app/agent/specialists.py`)
Five independent checks, each returning `list[SpecialistFinding]` with category, severity, confidence, evidence, and assumptions:

- `check_clearances` - dining table spatial footprint conflict
- `check_daylight` - missing orientation blocks daylight assessment
- `check_privacy` - primary bedroom privacy
- `check_circulation` - storage vs. circulation trade-off
- `check_adjacency` - kitchen / living visual connection obligations

### 6. Synthesizer (`app/agent/synthesizer.py`)
Converts findings into `Recommendation` objects (`{category} Review Action`), gating `requires_human_approval=True` for `high`-severity findings.

### 7. Agent Wiring (`app/main.py`)
`POST /v1/reviews` now runs the full pipeline: parse -> 5 specialists -> synthesize -> persist -> return `status='completed'`. GET / decisions routes now hit the in-memory store with 404 handling.

### 8. Test Suite (`tests/test_reviews.py`)
Three pytest cases covering the standard scenario, the human-approval decision flow, and 404 failure paths. All passing.

## Prompts & Direction

The system was built through a sequence of user prompts that drove the architecture:

1. **Schema definition** - User specified exact Pydantic v2 data models (fields, types, defaults, and the `accept`/`reject` constraint). Direction: single contract module, regex-validated enums.
2. **FastAPI scaffold** - User specified app title, health route, and three placeholder routes returning dummy responses. Direction: clean, modular, fully typed.
3. **In-memory state** - User specified a global dict store with save/get helpers keyed by `run_id`.
4. **Brief parser** - User specified deterministic, rule-based parsing outputting `structured_brief`, `missing_information` (critical flags), `contradictions`, and `clarification_questions`; explicitly required no external API failures (rule-based over LLM).
5. **Specialists** - User specified five domain checks and the exact test scenario (8-seat dining in 92 sq m) with severity, confidence, evidence, and assumptions requirements.
6. **Synthesizer** - User specified mapping of findings to recommendations including the human-approval gate.
7. **Agent wiring** - User specified the end-to-end orchestration in the route handlers including 404 handling and decision status updates.
8. **Tests** - User specified exactly three pytest functions and their assertions, mirroring the required acceptance scenarios.

## Required Evidence: AI Correction

**Incident:** During the initial schema generation step, the AI (OpenCode) produced the `Recommendation` model **without** the `requires_human_approval` field. The schema silently omitted the safeguard flag that is critical for routing high-severity findings through an architect's approval before any action is taken.

**Detection & Correction:** The user explicitly caught the omission in their prompt for the schema step and directed that the `Recommendation` model must include `requires_human_approval: bool`. The field was added to the contract, and the synthesizer was subsequently built so that findings with `severity == 'high'` set `requires_human_approval = True`, flagging them for the architect's review.

**Why this matters:** Without this field, the API would have no programmatic signal distinguishing reviewable vs. non-reviewable recommendations. The high-severity spatial conflict (8-seat dining table in a 92 sq m apartment) and the missing-orientation daylight finding would have been treated identically to routine notes, defeating the human-in-the-loop safeguard requirement.

**Verification:** `tests/test_reviews.py::test_standard_scenario_review` asserts that at least one recommendation carries `requires_human_approval == True`, locking the correction in as a regression guard.