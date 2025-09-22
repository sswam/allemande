# comparing my X11 gamma ramp tools

They are all stable and written in C.

## xdark

xdark is a simple command-line utility to adjust the brightness of your display in software. It allows you to darken or invert the colors of your screen, providing a way to reduce eye strain or create a specific visual effect.

*   Adjusts display brightness in software, similar to xgamma.
*   Can darken, or invert the display colors.
*   Takes arguments for target brightness (0.0-1.0), either a single value to darken to, or a "from" and "to" value.
*   Without arguments, it reads the current brightness values.
*   `-i` option inverts the display colors.

## xramp

xramp is a command-line utility to set the color ramp (gamma ramp) of your display using the X RandR extension. It allows you to adjust the red, green, and blue color channels independently, providing fine control over the display's color output. It probably should be rewritten in a scripting language.

*   Sets color ramp via system calls to `ramp-gen` and `ramp-io`.
*   `iclamp`: Clamps an integer within a specified range.
*   `ramp_range`: Converts a float to an integer within the range of 0-65535.
*   `xramp`: Takes pairs of floats for red, green, and blue (`r0`, `r1`, `g0`, `g1`, `b0`, `b1`), converts them to ramp values, and executes `ramp-gen` and `ramp-io`.
*   `main`: Parses command-line arguments to set the color ramp, allowing for single, dual, triple, or sextuple float arguments to control color values.  Displays usage if incorrect arguments are given.

## ramp-io

Minimal core functionality, intended to be used from scripts, rather than a standalone tool.

*   Initializes the X RandR extension to interact with display outputs.
*   Gets the current gamma ramps for each connected screen/CRTC.
*   Outputs the number of screens, ramp size, and the RGB gamma ramps to standard output.
*   Reads the same information (number of screens, ramp size, RGB gamma ramps) from standard input.
*   Restores the gamma ramps based on the input received from standard input.
*   Frees resources and disconnects from the X server.

In essence, it's a gamma ramp dumper/restorer via standard input/output, used to save/load display settings.
