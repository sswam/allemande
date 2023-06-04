To search Instagram for images, you will need to use Instagram's private API or a third-party library, as Instagram makes it hard to scrape data directly from their website. I recommend using the `instaloader` library. First, install it with pip:

```
pip install instaloader
```

Then add the following function to your script:

```python
import instaloader

def instagram_search(query, max_results=12, login_user=None, login_password=None):
	loader = instaloader.Instaloader(download_pictures=False)
	if login_user and login_password:
		loader.context.login(login_user, login_password)
	search_results = []

	for profile in instaloader.TopSearchResults(loader.context, query).get_profiles():
		if len(search_results) >= max_results:
			break
		result = {
			'username': profile.username,
			'profile_pic_url': profile.profile_pic_url,
			'profile_url': f"https://www.instagram.com/{profile.username}"
		}
		search_results.append(result)

	return search_results
```

Note that the function does not log in by default. You can provide a `login_user` and `login_password` if needed to access private profiles.

Now, you can integrate this function into your existing engines:

```python
engines = {
	'Google': google_search,
	'Instagram': instagram_search,
	'YouTube': youtube_search,
	'PornHub': pornhub_search,
}
```

Please note that this solution relies on the `instaloader` library, which may not work if Instagram decides to change their API or limit its usage.
