import requests
import json

# Replace with your WordPress site URL
url = "http://example.com/wp-json/wp/v2/posts"

# Replace with your username and password
auth = ('username', 'password')

headers = {'Content-Type': 'application/json'}

# Replace with your title, content, and category ID
data = {
    'title': 'Your Post Title',
    'content': 'Your Post Content',
    'categories': [12],  # 12 is the category ID
    'status': 'publish'
}

response = requests.post(url, headers=headers, data=json.dumps(data), auth=auth)

print(response.json())
