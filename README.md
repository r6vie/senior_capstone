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
- Responsive landing page, member directory, and profile editor

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
Credentials belong only in `.env`, which is ignored by Git.

## Run

Backend:

```sh
.venv/bin/python -m uvicorn main:app --app-dir backend --reload --host 127.0.0.1 --port 8000
```

Frontend (in another terminal):

```sh
npm --prefix frontend run dev
```

Open [the app](http://127.0.0.1:5173) or the [API docs](http://127.0.0.1:8000/docs).

## Tests

```sh
.venv/bin/python -m pip install -r backend/requirements-dev.txt
PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -v
npm --prefix frontend run build
```

Tests run without connecting to Atlas.

## Project status

The core account, profile, and directory flow is implemented. AI matching,
outreach generation, email verification, password reset, and CWRU SSO are future work.
