# FoundersCircle

A platform for discovering and connecting with people in the CWRU network.

## Tech stack

- Python, FastAPI, and Pydantic backend
- MongoDB Atlas with PyMongo
- React, TypeScript, and Vite frontend

## Features

- Sign up and log in with LinkedIn (the only way to create an account); password login remains for existing accounts
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

### LinkedIn sign-in

1. Create an app at [linkedin.com/developers](https://www.linkedin.com/developers/apps)
   and, under **Products**, request **Sign In with LinkedIn using OpenID Connect**.
2. Under **Auth**, add `http://127.0.0.1:5173/api/auth/linkedin/callback` as an
   authorized redirect URL (it must match exactly, including `127.0.0.1`).
3. Copy the Client ID and Client Secret into `LINKEDIN_CLIENT_ID` and
   `LINKEDIN_CLIENT_SECRET` in `.env`, then restart the backend.

We request the `openid profile email` scopes, which share a member's name, email,
and photo. Work history and skills need LinkedIn partner-program access.

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

The core account, profile, and directory flow is implemented, with LinkedIn sign-up.
AI-built profiles from LinkedIn data, AI matching, outreach generation, and CWRU SSO
are future work.
