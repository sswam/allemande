from starlette.requests import Request

def get_user(request: Request) -> str:
    """Get the user from the request headers."""
    user = request.headers["X-Forwarded-User"]
    # Attempt to decode the user header to UTF-8.
    try:
        user = user.encode('latin1').decode('utf-8')
    except (UnicodeDecodeError, UnicodeEncodeError):
        pass
    return user
