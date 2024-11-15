# auth

## overview

This is a basic auth service, consisting of:

1. login.html: A simple login form which doubles as a sign up form, password reset form, change password form.
   - name, email, password
   - also need username, display name
   - username and email must be unique
   - username and display name are not secret
2. auth.py: The auth service using FastAPI
   - Stores bcrypt password hashes in an .htpasswd file
   - Also adds users to the system in the /etc/passwd / /etc/shadow files, with shell /usr/sbin/nologin initially
   - They have a homedir /home/$username
   - User info and settings can be stored under the homedir, in private and public files

Save cookies for auth, need a cookie for each subdomain.



TODO Refresh tokens?

Refresh tokens are more secure because:
1. Access tokens are sent with every request and are more exposed to potential theft
2. If an access token is stolen, it gives limited time window for abuse
3. Refresh tokens are only sent once to get new access tokens, and can be blacklisted/revoked if compromised

Short-lived access tokens + long-lived refresh tokens = better security with good user experience.

Store both tokens as http-only cookies but:
1. Access token with short expiry (15min)
2. Refresh token with longer expiry (7days) and path restricted to only the refresh endpoint (/api/refresh)

This way refresh token is only sent when needed, not with every request.

Set cookie path like this:
```javascript
res.cookie('refreshToken', token, {
  httpOnly: true,
  path: '/api/refresh'
});
```
