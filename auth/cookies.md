Here's how to handle JSON data in cookies between Python/FastAPI and JavaScript:

**Python (FastAPI) - Setting the cookie:**
```python
from fastapi import FastAPI, Response
import json
from urllib.parse import quote

app = FastAPI()

@app.get("/set-cookie")
def set_cookie():
    # Example data to store in cookie
    data = {
        "user": "john",
        "preferences": {
            "theme": "dark",
            "language": "en"
        },
        "numbers": [1, 2, 3]
    }
    
    # Convert to JSON string and URL-encode
    json_str = json.dumps(data)
    encoded_data = quote(json_str)
    
    # Create response and set cookie
    response = Response()
    response.set_cookie(
        key="user_data",
        value=encoded_data,
        max_age=3600,  # Cookie expiration in seconds
        httponly=False  # Allow JavaScript access
    )
    
    return response
```

**JavaScript - Reading and parsing the cookie:**
```javascript
// Function to get cookie by name
function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) {
        return parts.pop().split(';').shift();
    }
    return null;
}

// Function to decode and parse JSON cookie
function getJSONCookie(name) {
    const cookieValue = getCookie(name);
    if (cookieValue) {
        try {
            // Decode URL-encoded string and parse JSON
            const decodedValue = decodeURIComponent(cookieValue);
            return JSON.parse(decodedValue);
        } catch (e) {
            console.error('Error parsing cookie:', e);
            return null;
        }
    }
    return null;
}

// Usage example
const userData = getJSONCookie('user_data');
if (userData) {
    console.log('User:', userData.user);
    console.log('Theme:', userData.preferences.theme);
    console.log('Numbers:', userData.numbers);
}
```

**HTML example to test:**
```html
<!DOCTYPE html>
<html>
<head>
    <title>Cookie Test</title>
</head>
<body>
    <button onclick="readCookie()">Read Cookie</button>
    
    <script>
        function readCookie() {
            const userData = getJSONCookie('user_data');
            if (userData) {
                console.log('Cookie data:', userData);
            } else {
                console.log('Cookie not found or invalid');
            }
        }
        
        // Include the JavaScript functions from above here
    </script>
</body>
</html>
```

Some important notes:

1. The Python code uses `quote()` from `urllib.parse` to URL-encode the JSON string, which handles special characters that might cause issues in cookies.

2. The cookie is set with `httponly=False` to allow JavaScript access. If you don't need JavaScript access, you should set this to `True` for better security.

3. You might want to add additional cookie parameters like:
   - `secure=True` (for HTTPS only)
   - `samesite="Strict"` or `samesite="Lax"` (for CSRF protection)
   - `path="/"` (to specify cookie scope)

4. The JavaScript code includes error handling for both cookie retrieval and JSON parsing.

5. Remember that cookies have size limitations (typically 4KB), so be careful with the amount of data you store.

To use this in a real application, you might want to add:

1. Data validation before storing
2. Error handling in the Python code
3. Compression if dealing with larger data
4. Security measures like signing the data to prevent tampering

Example usage with additional security:
```python
from fastapi import FastAPI, Response
import json
from urllib.parse import quote
from base64 import b64encode
import hmac
import hashlib

app = FastAPI()

SECRET_KEY = "your-secret-key"  # Store this securely

def sign_data(data: str) -> str:
    signature = hmac.new(
        SECRET_KEY.encode(),
        data.encode(),
        hashlib.sha256
    ).hexdigest()
    return f"{data}|{signature}"

@app.get("/set-cookie")
def set_cookie():
    data = {"user": "john"}
    json_str = json.dumps(data)
    signed_data = sign_data(json_str)
    encoded_data = quote(signed_data)
    
    response = Response()
    response.set_cookie(
        key="user_data",
        value=encoded_data,
        max_age=3600,
        httponly=False,
        secure=True,
        samesite="Lax"
    )
    
    return response
```

This provides a secure way to store and retrieve JSON data in cookies between your FastAPI backend and JavaScript frontend.

