# reaper: a sourceable script to ensure child processes are terminated when the command exit
# NOTE: the tests do not work yet!

# example:
# (. reaper; sleep 60 & sleep 300 & wait)

cleanup() {
    local exit_code=$?

    kill -TERM 0 2>/dev/null || true
    exit $exit_code
}

handle_signal() {
    local sig=$1
    exit $((128 + sig))
}

# Core signals we definitely want to handle
trap cleanup EXIT
trap 'handle_signal 1' HUP    # 129
trap 'handle_signal 2' INT    # 130
trap 'handle_signal 3' QUIT   # 131
trap 'handle_signal 13' PIPE  # 141
trap 'handle_signal 15' TERM  # 143

# Optional: trap all trappable signals
# for sig in $(seq 1 64); do
#     if [ $sig -ne 9 ] && [ $sig -ne 19 ] && [ $sig -ne 32 ] && [ $sig -ne 33 ]; then

#         trap "handle_signal $sig" $sig 2>/dev/null || true
#     fi
# done
