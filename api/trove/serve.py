"""The whole app as one web service, for hosting (docs/deploy.md).

The API answers under /api and the built website answers everywhere else, so the browser talks to one
address: no cross-site settings, and the website's own `/api/...` calls work as they do in development.
Run it with `uvicorn trove.serve:site`. For local work, `scripts/dev.py` is still the way.
"""

import os
from pathlib import Path

from fastapi import FastAPI
from starlette.exceptions import HTTPException
from starlette.staticfiles import StaticFiles

from trove.core.config import REPO_ROOT
from trove.main import app as api

# Where `npm run build` puts the website. The container copies it here.
DEFAULT_DIST = REPO_ROOT / "web" / "dist"
ONE_YEAR = 31_536_000


class SinglePageFiles(StaticFiles):
    """The built website. An address that isn't a file (a page like /checkouts) gets index.html and the
    app's router decides what to show; a missing file (a .js or .png) is a real 404."""

    async def get_response(self, path, scope):
        try:
            response = await super().get_response(path, scope)
        except HTTPException as error:
            if error.status_code != 404 or "." in Path(path).name:
                raise
            response = await super().get_response("index.html", scope)
        # Built asset names carry a hash of their contents, so they can be kept for good. The page that
        # names them must always be asked for again, or a new release wouldn't reach anyone.
        if path.replace("\\", "/").startswith("assets/"):
            response.headers["Cache-Control"] = f"public, max-age={ONE_YEAR}, immutable"
        else:
            response.headers["Cache-Control"] = "no-cache"
        return response


def build_site(dist: Path | None) -> FastAPI:
    # A mounted app's startup doesn't run by itself, so the site starts the API's (the database).
    site = FastAPI(
        lifespan=lambda _site: api.router.lifespan_context(api),
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    site.mount("/api", api)
    if dist is not None and (dist / "index.html").is_file():
        site.mount("/", SinglePageFiles(directory=dist), name="web")
    return site


site = build_site(Path(os.environ.get("TROVE_WEB_DIST") or DEFAULT_DIST))
