#!/bin/bash -eu
mail=${mail:-$HOME/mail}

# Check if any unread mail
if [ "$(ls -A "$mail/new")" ]; then
    notify-send -u critical "Unread Mail" "You have unread mail!"
fi

# wait for new mail
while inotifywait -e create "$mail/new"; do
    notify-send -u critical "New Mail" "You have new mail!"
done
