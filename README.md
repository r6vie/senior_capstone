# FoundersCircle

A platform for discovering and connecting with people in the CWRU network.

## Tech stack

- Python, FastAPI, and Pydantic backend
- MongoDB Atlas with PyMongo
- React, TypeScript, and Vite frontend

## Features

- Sign up and log in with LinkedIn or email and password
- Authenticated profile creation, viewing, editing, and deletion
- Profile ownership controls and expertise search
- Explainable need-based alumni matching and automatic recommendations
- Connection requests, messaging, and optional email notifications
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

The core account, LinkedIn sign-up, profile, directory, explainable matching,
AI onboarding, connection, messaging, and notification flows are implemented.
Semantic matching, outreach generation, password reset, and CWRU SSO are future work.
