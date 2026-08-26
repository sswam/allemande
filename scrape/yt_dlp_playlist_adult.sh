# needs soft/bgutil-ytdlp-pot-provider running
# needs cookies e.g. saved with "Get cookies.txt LOCALLY" extension
# For long lasting cookies, log in to youtube in an incognito window, go to youtube.com/robots.txt, save the cookies, then close the (all) incognito windows
CHANNEL="$1"
time yt-dlp --download-archive downloaded.txt --cookies www.youtube.com_cookies.txt --yes-playlist --extractor-args "youtubepot-bgutilhttp:base_url=http://127.0.0.1:4416" --extractor-args "youtube:player_client=mweb" --output "%(title).50s [%(id)s].%(ext)s" --remote-components ejs:github "https://www.youtube.com/@$CHANNEL"
