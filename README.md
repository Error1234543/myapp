# TOOLNEX

**One Platform. Hundreds of Tools.**

TOOLNEX is a mobile-first online utility platform. This repository starts with a Python FastAPI processing backend and a separate web frontend.

## Project layout

- `backend/` — FastAPI API and PDF, image, and text processing engines.
- `frontend/` — responsive Dark Premium 3D web interface.
- `Dockerfile` — container setup for Koyeb deployment.

## Local backend setup

```bash
cd backend
python -m venv .venv
# Activate the virtual environment, then:
pip install -r requirements.txt
uvicorn main:app --reload
```

Open `http://127.0.0.1:8000/docs` for the API test page.

## Deployment

Deploy this repository to Koyeb using the root `Dockerfile`. Configure `PORT` if the platform supplies one. Set `FRONTEND_ORIGINS` to the deployed frontend origin before public launch.

## Safety and privacy

The initial API validates uploads and processes files in memory. Do not upload confidential documents to an unverified deployment. Production deployment should add rate limits, request-size limits at the edge, monitoring, and a tested retention policy.
