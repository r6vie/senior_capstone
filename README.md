# FoundersCircle

A platform for discovering and connecting with people in the CWRU network.

## Tech stack

- Python, FastAPI, and Pydantic backend
- MongoDB Atlas with PyMongo
- React, TypeScript, and Vite frontend

## Features

- Email/password signup, login, and logout
- Authenticated profile creation, viewing, editing, and deletion
- Profile ownership controls and expertise search
- Explainable need-based alumni matching and automatic recommendations
- Responsive landing page, member directory, and profile editor
- Onboarding: a short basics form, then an AI interview (Claude) that saves what it
  learns as open-ended facts, each with its own visibility (everyone, matches only, or
  only me). Members review, edit, and delete facts as they go.

## Setup

MongoDB Atlas is already established. New contributors need authorized access to
the existing database; there is no need to create another cluster.

From the repository root:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements.txt
npm --prefix frontend install
```

Create a local `.env` using `.env.example` as a template, unless one already exists.
Set `MONGODB_URI` to your private connection string and
`MONGODB_DATABASE=founderscircle`. Ensure your IP is allowed in Atlas.
For the AI interview, also set `ANTHROPIC_API_KEY` (optionally `ANTHROPIC_MODEL`;
the default is `claude-opus-5-5`). Without a key, everything else still works and
the interview reports that it isn't set up.
Credentials belong only in `.env`, which is ignored by Git.

## Run

```sh
python3 scripts/dev.py
```

Open [the app](http://127.0.0.1:5173) or the [API docs](http://127.0.0.1:8000/docs).
The backend stays online and reconnects automatically after temporary Atlas outages.

## Tests

```sh
.venv/bin/python -m pip install -r backend/requirements-dev.txt
PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -v
npm --prefix frontend run build
```

Tests run without connecting to Atlas or calling Claude.

## Project status

The core account, profile, directory, explainable matching, and AI-driven onboarding
flows are implemented. Member facts retain per-fact visibility controls. Semantic AI
matching, outreach generation, email verification, password reset, and CWRU SSO are future work.
