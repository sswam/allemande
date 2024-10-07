# emcc -s WASM=1 -s SIDE_MODULE=1 -o $@ $<

# q. what do the WASM=1 -s SIDE_MODULE=1 flags do?
# a. WASM=1 tells emcc to generate a WebAssembly binary.
#   SIDE_MODULE=1 tells emcc to generate a WebAssembly binary that can be linked into a larger program.

#--include-in-header=script.html $< -o $@

# These options are not always necessary or optimal for every WebAssembly app:
# 
# 1. `-s WASM=1`: This is the default in recent Emscripten versions, so it's often unnecessary.
# 
# 2. `-s SIDE_MODULE=1`: This creates a side module without runtime dependencies. It's useful for dynamic linking but not needed for standalone WASM modules.
# 
# Use these options only when your specific use case requires them.
