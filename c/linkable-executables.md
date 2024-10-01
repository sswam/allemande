In C, can I tell the compiler to exclude main, so as to use the same source code both for a library and an executable?  Or can I make an executable which can also be linked as a library, excluding the main function while linking? I do not want to use preprocessor #if #ifdef or similar it leads to madness, I would rather tell the linker to skip main.

Yes, you can achieve this without preprocessor directives:

1. For a library:
   - Compile with `-fno-builtin-main` to prevent the compiler from treating `main` as special.
   - Use `-c` to compile to object files without linking.

2. For an executable:
   - Compile normally.

3. To use the same binary as both:
   - Compile with `-fno-builtin-main`
   - When linking as a library, use `--undefined=<alternative_entry_point>` to specify a different entry point.

This way, `main` is treated as a regular function, allowing flexibility in how the code is used.

