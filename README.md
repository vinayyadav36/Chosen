# Hybrid AI Interview Platform

A FastAPI-based hybrid interview platform supporting voice and text interview modes.

## Architecture

```text
Frontend (HTML/CSS/JS)
       |
FastAPI REST + WebSocket
       |
Interview Engine (Text/Voice Agents) + LLM Engine
       |
Scoring + Report Service + Resume/JD Parsers
       |
MongoDB (or in-memory fallback) + reports/*.pdf
```

## Setup

```bash
python -m pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Open `http://localhost:8000/frontend/index.html`.

## Environment Variables

See `.env.example`.

## API Reference

- `GET /api/health`
- `POST /api/interview/start`
- `POST /api/interview/{interview_id}/text-message`
- `WS /api/interview/{interview_id}/voice-stream`
- `GET /api/interview/{interview_id}/report`
- `POST /api/assessment/{interview_id}/recompute`

## Testing

```bash
pytest -q
```

## Docker

```bash
docker-compose up --build
```

## Deployment

`render.yaml` is included for Render deployment.

## Known limitations

- Voice path uses provider APIs and should be configured with valid keys.
- LLM behavior is heuristic-first with optional OpenAI client initialization.
