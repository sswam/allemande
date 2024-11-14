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

ht = HtpasswdFile(HTPASSWD)


async def http_exception(_request: Request, exc: HTTPException):
	""" Handle exceptions. """
	return JSONResponse({"error": exc.detail}, status_code=exc.status_code)


exception_handlers = {
	HTTPException: http_exception,
}


app = Starlette(exception_handlers=exception_handlers)


def create_jwt_token(email: str) -> str:
	"""Create a JWT token with the user's email"""
	payload = {
		"sub": email,
		"exp": datetime.utcnow() + timedelta(seconds=SESSION_MAX_AGE),
		"iat": datetime.utcnow(),
	}
	return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def set_cookies(response, jwt_token, user_data_value, max_age):
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
	data = await request.json()
	email, password = data['email'], data['password']
	ht.load_if_changed()
	is_valid = ht.check_password(email, password)
	if not is_valid:
		raise HTTPException(401, "Invalid email or password")

	# Create JWT token
	jwt_token = create_jwt_token(email)

	# Create response with both cookies
	user_data = {
		"email": email,
	}
	response = JSONResponse({})
	user_data_value = urllib.parse.quote(json.dumps(user_data))
	set_cookies(response, jwt_token, user_data_value, SESSION_MAX_AGE)

	return response


def verify_jwt_token(token: str) -> dict:
	try:
		payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
		return payload
	except jwt.ExpiredSignatureError:
		raise HTTPException(401, "Token has expired")
	except jwt.JWTError:
		raise HTTPException(401, "Invalid token")


# Key features of this implementation:
#
# 1. The JWT token includes:
# - Subject (`sub`): user's email
# - Expiration time (`exp`): when the token expires
# - Issued at time (`iat`): when the token was created
#
# 2. Security features:
# - `httponly=True` for the auth cookie prevents JavaScript access
# - `secure=True` ensures cookies are only sent over HTTPS
# - Domain is set to `.allemande.ai` for subdomain access
# - `samesite="lax"` helps prevent CSRF attacks
# - JWT token is signed with a secret key
#
# 3. The `user_data` cookie is URL-encoded JSON and accessible to JavaScript
#
# To use this in your application:
#
# 1. Install the required package:
# ```bash
# pip install pyjwt
# ```
#
# 2. Store the `JWT_SECRET` in environment variables rather than hardcoding it.
#
# 3. To verify the token in protected routes:
#
# ```python
# @app.route("/protected", methods=["GET"])
# async def protected_route(request):
# 	auth_cookie = request.cookies.get("auth")
# 	if not auth_cookie:
# 		raise HTTPException(401, "Not authenticated")
#
# 	payload = verify_jwt_token(auth_cookie)
# 	email = payload["sub"]
# 	# Continue with the protected route logic
# ```
#
# Remember to:
# - Use a strong, secure secret key
# - Store sensitive values in environment variables
# - Regularly rotate the JWT secret key
# - Consider implementing refresh tokens for longer sessions
# - Add rate limiting to the login endpoint
# - Add logging for security events


@app.route("/x/logout", methods=["POST"])
async def logout(request):
	# TODO: get email from session cookie if we need to know who is logging out
	response = JSONResponse({})
	# kill the cookies
	set_cookies(response, "", "", 0)
	return response


if __name__ == "__main__":
	uvicorn.run(app, host="127.0.0.1", port=8002)
