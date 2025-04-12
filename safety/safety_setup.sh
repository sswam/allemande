#!/bin/bash -eu

cd $ALLEMANDE_HOME/safety
[ -e nsfw_words ] ||
git clone https://github.com/LDNOOBW/List-of-Dirty-Naughty-Obscene-and-Otherwise-Bad-Words.git nsfw_words
