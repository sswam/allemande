*   Sets color ramp via system calls to `ramp-gen` and `ramp-io`.
*   `iclamp`: Clamps an integer within a specified range.
*   `ramp_range`: Converts a float to an integer within the range of 0-65535.
*   `xramp`: Takes pairs of floats for red, green, and blue (`r0`, `r1`, `g0`, `g1`, `b0`, `b1`), converts them to ramp values, and executes `ramp-gen` and `ramp-io`.
*   `main`: Parses command-line arguments to set the color ramp, allowing for single, dual, triple, or sextuple float arguments to control color values.  Displays usage if incorrect arguments are given.


