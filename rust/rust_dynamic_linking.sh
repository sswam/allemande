# Rust statically links its standard library by default for several reasons:
# 
# 1. Portability: Ensures consistent behavior across different systems.
# 2. Performance: Allows for better optimization.
# 3. Simplicity: Eliminates dependency issues.
# 
# However, you can opt for dynamic linking:
# 
# 1. Use `#![feature(rustc_private)]` for nightly builds.
# 2. Set `RUSTFLAGS='-C prefer-dynamic'` environment variable.
# 3. Use `-C prefer-dynamic` flag with rustc directly.
# 
# Note that dynamic linking may have limitations and is not recommended for most use cases.
# 
# This error occurs because the dynamic library for Rust's standard library is not in the system's library search path. To fix this:
# 
# 1. Find the library location:
#    `rustc --print sysroot`
# 
# 2. Add it to LD_LIBRARY_PATH:
#    `export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$(rustc --print sysroot)/lib`
# 
# 3. Run your command again.
# 
# Alternatively, use `rustc -C prefer-dynamic -C rpath` to embed the library path in the executable.


LD_LIBRARY_PATH=${LD_LIBRARY_PATH:+$LD_LIBRARY_PATH:}$(rustc -print sysroot)/lib

rustc -C prefer-dynamic "$progam"
