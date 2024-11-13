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
