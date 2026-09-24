# FoundersCircle

A platform for finding people in the CWRU network based on your profile and what
you need. This Python backend lets you create, retrieve, edit, delete, and search
profiles stored in MongoDB Atlas.
Users sign up with an email and password, then log in to access the network.

## First-time setup

Open a terminal in this project's folder and run:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements.txt
```

The first command creates a private Python environment for this project. The
second installs FastAPI (the framework), Uvicorn (the server), and MongoDB's
Python driver.

## Set up MongoDB Atlas

1. Create an account at <https://www.mongodb.com/cloud/atlas/register>.
2. Create a project called `FoundersCircle` and select a **Free / M0** cluster.
   The default provider and a nearby region are fine for development.
3. Create a database user and save its password. This is separate from your
   Atlas login. Give it read/write access to the `founderscircle` database.
4. Add **your current IP address** to the project's network access list.
5. Select your cluster's **Connect → Drivers → Python** option and copy the
   connection string.
6. Open `.env` in this project's root folder and paste the string after
   `MONGODB_URI=`. Replace any username/password placeholders with the database
   user's credentials. Keep `MONGODB_DATABASE=founderscircle`.

For a fresh checkout, create `.env` using `.env.example` as the template. The
`.env` file is ignored by Git: don't paste your real connection string into chat,
the README, or Python source files. If the password has special characters,
percent-encode them in the URI (for example, `@` becomes `%40`).

Official walkthroughs: [create a free cluster](https://www.mongodb.com/docs/atlas/tutorial/deploy-free-tier-cluster/)
and [connect your application](https://www.mongodb.com/docs/atlas/connect-to-database-deployment/).

## Save the sample profiles

Once `.env` is filled in, run this from the project's folder:

```sh
.venv/bin/python backend/seed.py
```

This checks the connection and inserts our three fictional profiles. MongoDB
creates the `founderscircle` database and its `profiles` collection on the first
write. You can run this command again: existing sample profiles are neither
duplicated nor overwritten. In Atlas, use the data browser to view them.

## Run the backend

From the project's folder, run:

```sh
.venv/bin/python -m uvicorn main:app --app-dir backend --reload --host 127.0.0.1 --port 8000
```

Keep that terminal open while using the backend. Visit:

- <http://127.0.0.1:8000> to see the welcome message.
- <http://127.0.0.1:8000/health/database> to verify the live MongoDB connection.
- <http://127.0.0.1:8000/profiles/sample> to see a fictional person's profile.
- <http://127.0.0.1:8000/profiles> to see all three fictional profiles.
- <http://127.0.0.1:8000/profiles?expertise=mentoring> to find the two people with
  mentoring expertise.
- <http://127.0.0.1:8000/docs> to try the endpoint in FastAPI's interactive documentation.

The profile and database-health endpoints require login now. Opening them directly
in the browser address bar returns **401** because it does not send your login
token. Use the docs' **Authorize** button as described below to try them.

The home page should return:

```json
{"message": "FoundersCircle backend is running."}
```

Press `Control+C` in the terminal to stop the server. The `--reload` option
automatically reloads the application when you save changes to the Python code.
If port 8000 is already in use, change `--port 8000` to `--port 8001` and use 8001
in the browser addresses too.

Restart the backend after editing `.env`; Python's auto-reload does not watch
that file. The home page and `/docs` work before MongoDB is configured. Requests
without a login token return 401 on protected endpoints. Authenticated operations
and signup/login need MongoDB and return HTTP 503 when it is unavailable. Invalid
connection configuration or index creation failures can prevent startup.
An empty connected database returns `[]` for `/profiles` and 404
for `/profiles/sample` until you run the seed command.

If a connection fails, check the database user's credentials, whether your
current IP is allowed in Atlas, and whether the cluster is running. The backend
does not fall back to in-memory profiles. After seeding, profiles persist in
Atlas when you restart Python.

## Sign up and log in

In <http://127.0.0.1:8000/docs>:

1. Open **POST /auth/signup → Try it out**. Enter your name, email, and a password
   between 12 and 128 characters. Click **Execute**. A **201** response means
   your account was created. Account emails are case-insensitive and unique.
2. Open **POST /auth/login → Try it out**. Enter the same email and password.
   The **200** response contains an `access_token`.
3. Copy only that token's value, without quotation marks. Click **Authorize** at
   the top of the docs, paste it into the field, click **Authorize**, then **Close**.
   Do not type `Bearer` before it; the docs add that for you.
4. Try **GET /auth/me** to see your account. The docs now send your login token
   with protected requests, so you can search and create your profile.
5. Use **POST /auth/logout** to invalidate that session. The docs' own Logout
   button only forgets its local copy of the token; it does not revoke the session
   on the backend. After revoking, log in again to get a new token.

| Endpoint | Purpose | Login required? |
| --- | --- | --- |
| `POST /auth/signup` | Create a platform account | No |
| `POST /auth/login` | Get a one-hour login token | No |
| `GET /auth/me` | View your own account | Yes |
| `POST /auth/logout` | Revoke the current login token | Yes |
| `GET /profiles/me` | Find your own profile and its ID | Yes |
| All other `/profiles` endpoints | Search, validate, and manage profiles | Yes |
| `GET /health/database` | Check the database connection | Yes |

Signing up creates an account, not a network profile. Use **POST /profiles** after
login to create your profile. Each account may own one profile at a time; a second
creation returns **409**. `GET /profiles/me` returns **404** until you create one.
All members can view and search network profiles, but only their owner can edit
or delete them. A request targeting someone else's profile returns **404** and
does not change it. Deleting your profile does not delete your account.

The original fictional profiles have no owner and remain read-only through the
API. Existing profiles are not automatically assigned to new accounts. A database
administrator would need a separate, explicit ownership migration for real legacy data.

## How accounts are stored

- `users`: account details and Argon2 password hashes; never plaintext passwords.
- `sessions`: hashes of random login tokens, user IDs, and one-hour expiry times.
- `auth_attempts`: short-lived counters limiting signup/login attempts.
- `profiles`: network information with a server-assigned `owner_user_id`.

Session validity and active account membership are checked on every protected
request. MongoDB cleans up expired sessions with a TTL index; the API also checks
the expiration itself, so cleanup delays cannot extend a login. Logout revokes
only the current session. Tokens and account passwords must be kept private.

Startup creates unique indexes on account emails, token hashes, and profile
ownership, so concurrent requests cannot bypass these constraints. Profiles with
no owner are excluded from the unique ownership index.

Signup allows 5 attempts per IP per hour; login allows 10 per IP per 15 minutes.
These fixed-window counters are shared across workers and survive restarts.
Exceeding the limit returns **429** with a `Retry-After` header. Shared networks
share a limit. Proxy/client-IP handling must be configured for the chosen cloud
host before deployment.

This version verifies registered account credentials, not email ownership or
CWRU affiliation. Email verification, password reset, and CWRU SSO are not yet
implemented. Continue using localhost for development; a public deployment
requires HTTPS and an appropriate frontend session-storage strategy.

References: [FastAPI password hashing](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/),
[OWASP session guidance](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html),
and [MongoDB TTL indexes](https://www.mongodb.com/docs/manual/core/index-ttl/).

## Search by expertise

The `?expertise=mentoring` part of the address is a query parameter: it tells the
backend what to search for. Try changing `mentoring` to `medical` or `software`.
This is a simple text filter on the expertise labels, not AI matching yet.

Search ignores capitalization and spaces at the start or end. Leaving expertise
out (or blank) returns everyone, up to 100 profiles. A search with no matches returns `[]`, an empty
list. You can also use the **Try it out** button for `GET /profiles` in `/docs`.

## Create, edit, and delete profiles

Open <http://127.0.0.1:8000/docs> and use **Try it out** on these endpoints:
Sign in and use **Authorize** first.

| Endpoint | Purpose | Success |
| --- | --- | --- |
| `POST /profiles` | Validate and save your own profile | 201, saved profile |
| `GET /profiles/{profile_id}` | Retrieve one profile by its ID | 200, saved profile |
| `PATCH /profiles/{profile_id}` | Change fields on your own profile | 200, updated profile |
| `DELETE /profiles/{profile_id}` | Permanently remove your own profile | 204, no body |

For **POST /profiles**, send all five fields:

```json
{
  "name": "Jamie Chen (fictional)",
  "affiliation": "CWRU student",
  "location": "Cleveland, Ohio",
  "expertise": ["Python", "Data analysis"],
  "interests": ["Entrepreneurship"]
}
```

The response includes a server-generated `id`. Copy it into `profile_id` when
trying GET, PATCH, or DELETE. The list and sample endpoints now also include
`id` in each profile. IDs are strings; the existing seed profile IDs such as
`sample-alex` still work. You cannot choose or change an ID in request bodies.

For **PATCH**, send only what you want to change, for example:

```json
{"location": "Boston, Massachusetts"}
```

The name, affiliation, expertise, and interests remain unchanged. Send an empty
list (`[]`) to clear expertise or interests. Empty update bodies, explicit
`null`, blank text, unknown fields, and wrong types return **422** without writing
changes. Unknown IDs return **404** for GET, PATCH, and DELETE. Deleting the
same ID a second time returns 404 too. Database failures return **503**.

These endpoints really change MongoDB; use your own newly created fictional
profile when practicing deletion. The API still runs on `127.0.0.1` for local
development.

The update uses [FastAPI's partial-update pattern](https://fastapi.tiangolo.com/tutorial/body-updates/)
and MongoDB's `$set` operation to preserve fields omitted from the request.

## Where the code lives

- `backend/main.py`: defines the API endpoints and reads profiles from MongoDB.
- `backend/auth.py`: handles signup, login, sessions, and authentication.
- `backend/auth_models.py`: defines account and credential validation rules.
- `backend/models.py`: defines the Pydantic rules for valid profile data.
- `backend/database.py`: reads the private settings and manages the connection.
- `backend/sample_data.py`: contains the three fictional profiles for seeding.
- `backend/seed.py`: saves those profiles to MongoDB when explicitly run.
- `backend/requirements.txt`: lists the Python packages it needs.
- `.env`: holds your private MongoDB connection string.

Each profile is a MongoDB document: named fields such as `name` and `expertise`,
paired with their values. Documents live in the `profiles` collection inside the
`founderscircle` database. FastAPI reads them and sends JSON to your browser.
The initial seed records are fictional data for development.

## Try Pydantic validation in your browser

Pydantic checks that profile data follows our rules. FastAPI uses the `Profile`
model both for the validation endpoint's input and for the profiles it returns.
The test suite checks that these rules work; Pydantic itself is not a test runner.

1. Open <http://127.0.0.1:8000/docs> and sign in using the steps above.
2. Expand **POST /profiles/validate** and click **Try it out**.
3. Leave the provided fictional example in place and click **Execute**. Expect
   **200** and the validated profile.
4. Change `name` to `""` and execute again. Expect **422** with an error pointing
   to `name`.
5. Try changing `expertise` from a list to `"mentoring"`. Expect **422**, because
   it must be a list such as `["mentoring"]`.

The endpoint only validates and returns profile data; it never saves a profile
to MongoDB. It requires a valid login, which is checked in MongoDB. All five
profile fields are required.
Name, affiliation, location, and each expertise/interest entry must be nonblank
strings. Surrounding whitespace is removed. Empty expertise/interest lists are
allowed. Unknown fields and incorrect types are rejected. For validation or
creation, send only those five fields, without the `id` returned for saved profiles.

The existing `GET /profiles` and `GET /profiles/sample` endpoints validate their
MongoDB results too. Invalid stored data is a server error (500), whereas invalid
input to `POST /profiles/validate` is a request error (422).

References: [Pydantic models](https://docs.pydantic.dev/latest/concepts/models/)
and [FastAPI response validation](https://fastapi.tiangolo.com/tutorial/response-model/).

## Development checks

```sh
.venv/bin/python -m pip install -r backend/requirements-dev.txt
PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -v
```

These checks use test doubles and do not connect to Atlas. They cover validation,
CRUD, credential handling, protected routes, ownership, rate limits, and indexes.
Sign in through `/docs` and execute `/health/database` to verify your real connection.
