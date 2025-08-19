# completely blank an xterm
# intended to save OLED!
trap 'tput cnorm' EXIT
clear; tput civis ; read
