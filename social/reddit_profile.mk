#!/usr/bin/make -f

# Profile a Reddit user based on recent public posts and comments

# Check if user variable is set
ifndef user
$(error Usage: make -f reddit_profile.mk user=USERNAME)
endif

# Set SSH command based on hostname
ifeq ($(HOSTNAME),$(ALLEMANDE_HOME_HOSTNAME))
SSH :=
else
SSH := $(ALLEMANDE_HOME_HOSTNAME) --
endif

# Define targets
.PHONY: all clean

all: $(user).s

# Download JSON data
$(user).json:
	$(SSH) wget -O $@ https://www.reddit.com/user/$(user)/.json

# Extract text from JSON
$(user).txt: $(user).json
	jq -r '.data.children.[].data | .subreddit,.link_title,.selftext,.body' $< | \
	grep -v '^null$$' > $@

# Process and filter text
$(user).filtered.txt: $(user).txt
	uniqo < $< | grep -v -e '^[-0-9]' -e ' icon$$' > $@

# Generate summary
$(user).s: $(user).filtered.txt
	process -m=flasho "Please summarise what we know about this Reddit user *$(user)* from their public profile, you can extrapolate and psychoanalyse a little! Don't be too kind with it, please, be objective. Include mention of opinions about men / women / gender please, if known; although not in a specific section. And please identify or take a guess at the user's gender and orientation." < $< | tee $@

clean:
	rm -f $(user).json $(user).txt $(user).filtered.txt $(user).s
