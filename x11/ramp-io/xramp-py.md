*   Generates and applies a color ramp to the system.
*   Takes 0, 1, 2, 3, or 6 float arguments (0.0 to 1.0) to define the ramp's color range.
*   Uses `ramp_gen` to generate the ramp data and `ramp_io` to apply it.
*   Arguments define:
    *   No args: Default ramp (0 to 1 for all channels).
    *   1 arg: Sets all channels to a ramp from 0 to the specified value.
    *   2 args: Sets all channels to a ramp between the two specified values.
    *   3 args: Sets red, green, and blue channels to ramps from 0 to the specified values, respectively.
    *   6 args: Sets red, green, and blue channels to ramps between the specified start and end values, respectively (r0 r1 g0 g1 b0 b1).
*   Clamps input values to the valid range (0-1, converted to 0-65535).


