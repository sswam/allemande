CGROUP_PATH="/sys/fs/cgroup/$CGROUP"

# Create the shared remote users cgroup if it doesn't exist
if [ -d "$CGROUP_PATH" ]; then
	exit 0
fi

mkdir -p "$CGROUP_PATH"
echo "$MEMORY_MAX" > "$CGROUP_PATH/memory.max"
echo "$SWAP_MAX" > "$CGROUP_PATH/memory.swap.max"
echo "$CPU_QUOTA" > "$CGROUP_PATH/cpu.max"
echo "$PROCESSES" > "$CGROUP_PATH/pids.max"
