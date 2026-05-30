# Chosen - Voice Interview Platform

## Run locally

```bash
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

## API

- `POST /api/interview/start`
- `WS /api/interview/{interview_id}/stream`
- `GET /api/interview/{interview_id}/report`
- `GET /health`

## Tests

```bash
pytest -q
```
