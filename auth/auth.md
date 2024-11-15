Key features of this implementation:

1. The JWT token includes:
- Subject (`sub`): user's email
- Expiration time (`exp`): when the token expires
- Issued at time (`iat`): when the token was created

2. Security features:
- `httponly=True` for the auth cookie prevents JavaScript access
- `secure=True` ensures cookies are only sent over HTTPS
- Domain is set to `.allemande.ai` for subdomain access
- `samesite="lax"` helps prevent CSRF attacks
- JWT token is signed with a secret key

3. The `user_data` cookie is URL-encoded JSON and accessible to JavaScript

To use this in your application:

1. Install the required package:
```bash
pip install pyjwt
```

2. Store the `JWT_SECRET` in environment variables rather than hardcoding it.

3. To verify the token in protected routes:

```python
@app.route("/protected", methods=["GET"])
async def protected_route(request):
	auth_cookie = request.cookies.get("auth")
	if not auth_cookie:
		raise HTTPException(401, "Not authenticated")

	payload = verify_jwt_token(auth_cookie)
	email = payload["sub"]
	# Continue with the protected route logic
```

Remember to:
- Use a strong, secure secret key
- Store sensitive values in environment variables
- Regularly rotate the JWT secret key
- Consider implementing refresh tokens for longer sessions
- Add rate limiting to the login endpoint
- Add logging for security events


Required flows:
1. Login: `<username> <password> [Continue] [Forgot?]`
2. Join: `<username> <password> [Continue]` → `<email> [Join] [Back]`
3. Forgot: `<username/email> [Send Reset Link]`
4. Reset: `<new_password> <confirm> [Reset]` (via email link)
5. Settings (when logged in): `[Change Email] [Change Password]`
   - Change Email: `<new_email> [Update]`
   - Change Password: `<old> <new> <confirm> [Update]`
   - Delete Account
   - Logout

Username preferred over email for login (shorter, more memorable, privacy).
