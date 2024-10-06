#!/bin/bash
# fullname-set: set the user's fullname
read -p "Your full name: " fullname
sudo chfn -f "$fullname" "$USER"
