from starlette.applications import Starlette
from starlette.responses import HTMLResponse, JSONResponse, RedirectResponse
from starlette.routing import Route
from starlette.middleware import Middleware
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.authentication import (
    SimpleUser,
    UnauthenticatedUser,
    requires,
    AuthenticationBackend,
)
import supabase_py
import jwt
import os
import logging
import json

from dotenv import load_dotenv

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(message)s")
load_dotenv()

# Configure Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_API_KEY = os.getenv("SUPABASE_API_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")
supabase = supabase_py.create_client(SUPABASE_URL, SUPABASE_API_KEY)

# Authentication
class SupabaseAuthBackend(AuthenticationBackend):
    async def authenticate(self, request):
        if "Authorization" not in request.headers:
            return None

        try:
            token = request.headers["Authorization"].replace("Bearer ", "")
            decoded_token = jwt.decode(token, options={"verify_signature": False})
            user_id = decoded_token["sub"]
            return SimpleUser(user_id)
        except Exception as e:
            return None

def decode_jwt(token, secret):
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        logger.info(f"Payload: {payload}")
        return payload
    except jwt.InvalidTokenError:
        logger.info("Invalid token")
        return None

# Homepage
# @requires("authenticated", redirect="login")
async def homepage(request):
    data = await request.body()
    logger.info("homepage request %r", data)
    html = """
    <html>
        <head>
            <title>Hello, world!</title>
        </head>
        <body>
            <h1>Hello, world!</h1>
        </body>
    </html>
    """
    return HTMLResponse(html)

# Login page
async def login(request):
    if request.method == "POST":
        form = await request.form()
        email = form.get("email")
        password = form.get("password")
        response = supabase.auth.sign_in(email=email, password=password)
        logger.info("superbase response %s", json.dumps(response, indent=4))
        # TODO I think we need try/except here
        decoded = jwt.decode(response["access_token"], SECRET_KEY, algorithms=["HS256"], audience="authenticated", verify=True)
        logger.info("decoded jwt: %s", json.dumps(decoded, indent=4))
        error = response.get("error")
        if error is None:
            # TODO set HTTP-only cookie or something
            return RedirectResponse(url="/")
    else:
        error = None

    html = f"""
    <html>
        <head>
            <title>Login</title>
        </head>
        <body>
            <h1>Login</h1>
            <form method="post">
                <label>Email:</label>
                <input type="email" name="email" required />
                <br />
                <label>Password:</label>
                <input type="password" name="password" required />
                <br />
                <input type="submit" value="Log in" />
            </form>
            <p><a href="/signup">Don't have an account? Sign up here.</a></p>
            {f'<p>{error}</p>' if error else ''}
        </body>
    </html>
    """
    return HTMLResponse(html)

# Sign up page
async def signup(request):
    if request.method == "POST":
        form = await request.form()
        email = form.get("email")
        password = form.get("password")
        response = supabase.auth.sign_up(email=email, password=password)
        if response.get("error") is None:
            return RedirectResponse(url="/login")
        else:
            error = response["error"]["message"]
    else:
        error = None

    html = f"""
    <html>
        <head>
            <title>Sign up</title>
        </head>
        <body>
            <h1>Sign up</h1>
            <form method="post">
                <label>Email:</label>
                <input type="email" name="email" required />
                <br />
                <label>Password:</label>
                <input type="password" name="password" required />
                <br />
                <input type="submit" value="Sign up" />
            </form>
            <p><a href="/login">Already have an account? Log in here.</a></p>
            {f'<p>{error}</p>' if error else ''}
        </body>
    </html>
    """
    return HTMLResponse(html)

routes = [
    Route("/", endpoint=homepage, methods=["GET", "POST"]),
    Route("/login", endpoint=login, methods=["GET", "POST"]),
    Route("/signup", endpoint=signup, methods=["GET", "POST"]),
]

middleware = [
    Middleware(AuthenticationMiddleware, backend=SupabaseAuthBackend())
]

app = Starlette(routes=routes, middleware=middleware)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
