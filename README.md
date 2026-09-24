# FoundersCircle

A platform in development for discovering and connecting with people in the CWRU
network. This repository currently contains the backend API.

## Tech stack

- Python, FastAPI, and Pydantic
- MongoDB Atlas with PyMongo
- React and TypeScript frontend planned

## Features

- Email/password signup, login, and logout
- Authenticated profile creation, viewing, editing, and deletion
- Profile ownership controls and expertise search
- Pydantic validation and automated tests

## Setup

MongoDB Atlas is already established. New contributors need authorized access to
the existing database; there is no need to create another cluster.

From the repository root:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements.txt
```

Create a local `.env` using `.env.example` as a template, unless one already exists.
Set `MONGODB_URI` to your private connection string and
`MONGODB_DATABASE=founderscircle`. Ensure your IP is allowed in Atlas.
Credentials belong only in `.env`, which is ignored by Git.

## Run

```sh
.venv/bin/python -m uvicorn main:app --app-dir backend --reload --host 127.0.0.1 --port 8000
```

Open [API docs](http://127.0.0.1:8000/docs) to explore the endpoints.
Sign up through `/auth/signup`, log in through `/auth/login`, then paste the
returned `access_token` into **Authorize** to use protected endpoints.
Restart the server after changing `.env`.

## Tests

```sh
.venv/bin/python -m pip install -r backend/requirements-dev.txt
PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -v
```

Tests run without connecting to Atlas.

## Project status

The backend runs locally with the existing cloud database. The frontend, AI
matching, outreach generation, email verification, password reset, and CWRU SSO
are not implemented yet.
