# Architecture contracts

## Rate limiting

- **IP** — only in nginx (`infra/configs/nginx_auth/`). Do not duplicate in Python.
- **email / phone hash** — FastAPI + Redis (`src/repositories/rate_limit.py`).
