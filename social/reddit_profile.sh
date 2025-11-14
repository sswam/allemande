#!/bin/bash
# Profile a Reddit user based on recent public posts and comments
if [ "$HOSTNAME" = "$ALLEMANDE_HOME_HOSTNAME" ]; then
	ssh=
else
	ssh="$ALLEMANDE_HOME_HOSTNAME --"
fi
user=$1
$ssh wget -O- https://www.reddit.com/user/$user/.json | tee "$user.json" | jq -r '.data.children.[].data | .subreddit,.link_title,.selftext,.body' | grep -v '^null' | tee "$user.txt" |
uniqo | grep -v -e '^[-0-9]' -e ' icon$' |
process -m=flasho "Please summarise what we know about this Reddit user *$user* from their public profile, you can extrapolate and psychoanalyse a little\! Don't be too kind with it, please, be objective. Include mention of opinions about men / women / gender please, if known; although not in a specific section." | tee "$user.s"
