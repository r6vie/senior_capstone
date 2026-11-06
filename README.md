# Trove

**Everyone has a book in them.** Trove is a networking web app for CWRU students and alumni. An AI
interview finds the book you could write, and other members check it out, which means a short
conversation with you.

- Product plan: [docs/trove.md](docs/trove.md)
- Work plan and assignments: [docs/plan.md](docs/plan.md)
- How the code is organized: [docs/architecture.md](docs/architecture.md)
- How to contribute (people and AI agents): [CONTRIBUTING.md](CONTRIBUTING.md)

The FoundersCircle code this replaced is preserved at the git tag `founderscircle-v1`.

## Setup

You need [uv](https://docs.astral.sh/uv/), Node 22 and Python 3.13.

```bash
uv sync --directory api
npm --prefix web install
cp .env.example .env
```

In `.env`, set:

- `MONGODB_URI`: ask a teammate for access to the shared Atlas cluster, and make sure your IP is
  allowed in Atlas.
- `MONGODB_DATABASE`: `trove_dev_<yourname>`, so your data never collides with a teammate's.
- `ANTHROPIC_API_KEY`: only needed for the AI features.

## Run

```bash
python3 scripts/dev.py
```

The app opens on http://127.0.0.1:5173, with the API docs on http://127.0.0.1:8000/docs.

## Check

```bash
python3 scripts/check.py
```

This runs the same lint, tests, type-check and build as CI.

## License

MIT. See [LICENSE](LICENSE).
