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

## Development Guide

### Adding New Agents
We follow a strict ABN (Agentic Bidirectional Negotiation) pattern.
See [Agent Template & Standard Procedure](Project Docs/Agent_Template.md) for instructions on creating, registering, and wiring up new agents.

### Agent Knowledge Bases
Each agent is equipped with a specific JSON-based Knowledge Base in `backend/knowledge/`.
This allows them to ground their decisions in domain-specific data.

- **Propulsion Agent:** `propulsion_db.json` (Parts inventory)
- **Safety Agent:** `safety_regulations.json` (Limits & margins)
- **QA Agent:** `security_vulns.json` (Common CWEs)
- **Engineering Core:** `engineering_best_practices.json` (Python/Physics patterns)
- **Analysis Core:** `physics_constants.json` (Units & constants)

To add knowledge, simply edit the corresponding JSON file. The agents load it dynamically.
