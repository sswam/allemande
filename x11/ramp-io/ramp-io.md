`ramp-io` is a C program that:

*   Initializes the X RandR extension to interact with display outputs.
*   Gets the current gamma ramps for each connected screen/CRTC.
*   Outputs the number of screens, ramp size, and the RGB gamma ramps to standard output.
*   Reads the same information (number of screens, ramp size, RGB gamma ramps) from standard input.
*   Restores the gamma ramps based on the input received from standard input.
*   Frees resources and disconnects from the X server.

In essence, it's a gamma ramp dumper/restorer via standard input/output, used to save/load display settings.


