# Beam.me

Engineering work you can see, trust, reuse, and improve — with humans always in the loop.

## Structure

- **frontend/**: React + Vite + Tailwind CSS + Framer Motion.
  - The web interface for Problem Composer, Live Pipeline, and Results.
- **backend/**: FastAPI (Python).
  - Orchestrates agents, manages state, and handles execution.
- **beam-user-code/**: (External Repo) Where generated code lives.

## Setup

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

## Environment Variables

See `.env` files in `frontend/` and `backend/`.

## Deployment

Designed for Vercel (frontend) and containerized backend.
# core
# core
