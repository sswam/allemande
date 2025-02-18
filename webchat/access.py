#!/usr/bin/env python3-allemande

"""
Nginx auth_request access control server that checks allow and deny lists in access.yml.
"""

from pathlib import Path
import yaml
from starlette.applications import Starlette
from starlette.responses import Response
from starlette.routing import Route
from uvicorn import run

from ally import main, logs  # type: ignore

__version__ = "0.1.1"

logger = logs.get_logger()


def find_access_file(path: Path) -> Path | None:
    """Search for access.yml in current and parent directories."""
    while path != path.parent:
        access_file = path / "access.yml"
        if access_file.exists():
            return access_file
        path = path.parent
    return None


# TODO use access check from chat.py, with parent files
# TODO don't crash the whole service if a file is invalid, just deny access to that directory
#   good luck to the user fixing it, if it's a user-controlled file!

def load_access_config(path: str) -> dict:
    """Load and validate the access configuration."""
    request_path = Path(path).resolve()
    access_file = find_access_file(request_path)

    if not access_file:
        logger.warning("No access.yml found for %s", path)
        return {}

    with open(access_file, encoding='utf-8') as f:
        config = yaml.safe_load(f)

    if not isinstance(config, dict):
        raise ValueError(f"Invalid access.yml format in {access_file}")

    return config


def check_access(user: str, path: str) -> bool:
    """Check if user has access based on allow/deny lists."""
    config = load_access_config(path)

    if not config:
        logger.info("No access rules found for %s, allowing access", path)
        return True

    allow = config.get("allow", None)
    deny = config.get("deny", [])

    if user in deny:
        logger.info("User %s denied by explicit deny rule", user)
        return False

    if allow is None:
        logger.info("No allow list specified, allowing access")
        return True

    if user in allow:
        logger.info("User %s allowed by explicit allow rule", user)
        return True

    logger.info("User %s not in allow list", user)
    return False


async def auth(request):
    """Handle nginx auth_request authentication."""
    user = request.headers.get("Remote-User")
    original_uri = request.headers.get("X-Original-URI", "/")

    if not user:
        logger.warning("No Remote-User header present")
        return Response(status_code=401)

    if check_access(user, original_uri):
        return Response(status_code=200)

    return Response(status_code=403)


def create_app():
    """Create the Starlette application."""
    routes = [Route("/auth", auth)]
    return Starlette(routes=routes)


def run_server(host: str = "localhost", port: int = 8080) -> None:
    """Run the access control server."""
    logger.info("Starting access control server on %s:%d", host, port)
    app = create_app()
    run(app, host=host, port=port)


def setup_args(arg):
    """Set up the command-line arguments."""
    arg("--host", default="localhost", help="Host to bind to")
    arg("--port", type=int, default=8080, help="Port to listen on")


if __name__ == "__main__":
    main.go(run_server, setup_args)
