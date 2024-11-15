#!/usr/bin/env python3-allemande

""" A simple authentication API. """

import os
import urllib
import json
from datetime import datetime, timedelta

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.exceptions import HTTPException
import uvicorn
import jwt
from passlib.apache import HtpasswdFile


SESSION_MAX_AGE = 30 * 24 * 3600  # 30 days
JWT_ALGORITHM = "HS256"

JWT_SECRET = os.environ["ALLYCHAT_JWT_SECRET"]
HTPASSWD = os.environ["ALLYCHAT_PASSWD"]

htpasswd = HtpasswdFile(HTPASSWD)


async def http_exception(_request: Request, exc: HTTPException):
	""" Handle exceptions. """
	return JSONResponse({"error": exc.detail}, status_code=exc.status_code)


exception_handlers = {
	HTTPException: http_exception,
}


app = Starlette(exception_handlers=exception_handlers)


def create_jwt_token(username: str) -> str:
	"""Create a JWT token with the username"""
	payload = {
		"sub": username,
		"exp": datetime.utcnow() + timedelta(seconds=SESSION_MAX_AGE),
		"iat": datetime.utcnow(),
	}
	return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def set_cookies(response, jwt_token, user_data, max_age):
	"""Set JWT auth and user data cookies"""
	user_data_value = urllib.parse.quote(json.dumps(user_data))
	# Set JWT auth cookie
	response.set_cookie(
		key="auth",
		value=jwt_token,
		max_age=max_age,
		httponly=True,           # Prevent JavaScript access
		secure=True,             # HTTPS only
		domain=".allemande.ai",  # Allow subdomains
		samesite="lax"           # Protect against CSRF
	)

	# Set user data cookie
	response.set_cookie(
		key="user_data",
		value=user_data_value,
		max_age=max_age,
		httponly=False,  # Allow JavaScript access
		secure=True,
		domain=".allemande.ai",
		samesite="lax"
	)


@app.route("/x/login", methods=["POST"])
async def login(request):
	"""Login with username and password"""
	data = await request.json()
	username, password = data['username'], data['password']
	htpasswd.load_if_changed()
	is_valid = htpasswd.check_password(username, password)
	if not is_valid:
		raise HTTPException(401, "Invalid username or password")

	# Create JWT token
	jwt_token = create_jwt_token(username)

	# Create response with both cookies
	user_data = {
		"username": username,
	}
	response = JSONResponse({})
	set_cookies(response, jwt_token, user_data, SESSION_MAX_AGE)

	return response


@app.route("/x/logout", methods=["POST"])
async def logout(request):
	"""Logout by clearing cookies"""
	# TODO: get username from session cookie if we need to know who is logging out
	response = JSONResponse({})
	# kill the auth cookie and the user_data cookie.
	set_cookies(response, "", {}, 0)
	return response


def verify_jwt_token(token: str|None) -> dict:
	"""Verify the JWT token and return the payload"""
	if not token:
		raise HTTPException(401, "Not authenticated")
	try:
		payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
		return payload
	except jwt.ExpiredSignatureError:
		raise HTTPException(401, "Token has expired")
	except jwt.JWTError:
		raise HTTPException(401, "Invalid token")


@app.route("/x/protected", methods=["GET"])
async def protected_route(request):
	auth_cookie = request.cookies.get("auth")
	payload = verify_jwt_token(auth_cookie)
	username = payload["sub"]
	# Continue with the protected route logic
	return JSONResponse({"username": username})


if __name__ == "__main__":
	uvicorn.run(app, host="127.0.0.1", port=8002)


# nginx JWT auth
#   - build module from source
#   - configure nginx
#   - test
# TODO: join for new accounts
#   - need email in addition to username
#   - add to htpasswd
#   - add to Linux system account, with no shell
#   - check username format
#   - check email format
#   - check password strength
#   - send confirmation email
#   - create user home directory and files
#   - log in after confirmation
# - Set no-cache / no-store headers for all responses when logged in
# - Consider using refresh tokens, will complicate serving static files