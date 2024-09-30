## File: /home/sam/allemande/www/glXChooseFBConfig.md

# glXChooseFBConfig

## Name

glXChooseFBConfig - return a list of GLX frame buffer configurations that match the specified attributes

## C Specification

```c
GLXFBConfig* glXChooseFBConfig(
    Display* dpy,
    int screen,
    const int* attrib_list,
    int* nelements
);
```

## Parameters

- `dpy`: Specifies the connection to the X server.
- `screen`: Specifies the screen number.
- `attrib_list`: Specifies a list of attribute/value pairs. The last attribute must be None.
- `nelements`: Returns the number of elements in the list returned by glXChooseFBConfig.

## Description

glXChooseFBConfig returns GLX frame buffer configurations that match the attributes specified in `attrib_list`, or NULL if no matches are found. If `attrib_list` is NULL, then glXChooseFBConfig returns an array of GLX frame buffer configurations that are available on the specified screen. If an error occurs, no frame buffer configurations exist on the specified screen, or if no frame buffer configurations match the specified attributes, then NULL is returned. Use XFree to free the memory returned by glXChooseFBConfig.

All attributes in `attrib_list`, including boolean attributes, are immediately followed by the corresponding desired value. The list is terminated with None. If an attribute is not specified in `attrib_list`, then the default value (see below) is used (and the attribute is said to be specified implicitly). For example, if GLX_STEREO is not specified, then it is assumed to be False. For some attributes, the default is GLX_DONT_CARE, meaning that any value is OK for this attribute, so the attribute will not be checked.

Attributes are matched in an attribute-specific manner. Some of the attributes, such as GLX_LEVEL, must match the specified value exactly; others, such as GLX_RED_SIZE, must meet or exceed the specified minimum values. If more than one GLX frame buffer configuration is found, then a list of configurations, sorted according to the "best" match criteria, is returned. The match criteria for each attribute and the exact sorting order is defined below.

The interpretations of the various GLX visual attributes are as follows:

- **GLX_FBCONFIG_ID**: Must be followed by a valid XID that indicates the desired GLX frame buffer configuration. When a GLX_FBCONFIG_ID is specified, all attributes are ignored. The default value is GLX_DONT_CARE.

- **GLX_BUFFER_SIZE**: Must be followed by a nonnegative integer that indicates the desired color index buffer size. The smallest index buffer of at least the specified size is preferred. This attribute is ignored if GLX_COLOR_INDEX_BIT is not set in GLX_RENDER_TYPE. The default value is 0.

- **GLX_LEVEL**: Must be followed by an integer buffer-level specification. This specification is honored exactly. Buffer level 0 corresponds to the default frame buffer of the display. Buffer level 1 is the first overlay frame buffer, level two the second overlay frame buffer, and so on. Negative buffer levels correspond to underlay frame buffers. The default value is 0.

- **GLX_DOUBLEBUFFER**: Must be followed by True or False. If True is specified, then only double-buffered frame buffer configurations are considered; if False is specified, then only single-buffered frame buffer configurations are considered. The default value is GLX_DONT_CARE.

- **GLX_STEREO**: Must be followed by True or False. If True is specified, then only stereo frame buffer configurations are considered; if False is specified, then only monoscopic frame buffer configurations are considered. The default value is False.

- **GLX_AUX_BUFFERS**: Must be followed by a nonnegative integer that indicates the desired number of auxiliary buffers. Configurations with the smallest number of auxiliary buffers that meet or exceed the specified number are preferred. The default value is 0.

- **GLX_RED_SIZE, GLX_GREEN_SIZE, GLX_BLUE_SIZE, GLX_ALPHA_SIZE**: Each attribute, if present, must be followed by a nonnegative minimum size specification or GLX_DONT_CARE. The largest available total RGBA color buffer size (sum of GLX_RED_SIZE, GLX_GREEN_SIZE, GLX_BLUE_SIZE, and GLX_ALPHA_SIZE) of at least the minimum size specified for each color component is preferred. If the requested number of bits for a color component is 0 or GLX_DONT_CARE, it is not considered. The default value for each color component is 0.

- **GLX_DEPTH_SIZE**: Must be followed by a nonnegative minimum size specification. If this value is zero, frame buffer configurations with no depth buffer are preferred. Otherwise, the largest available depth buffer of at least the minimum size is preferred. The default value is 0.

- **GLX_STENCIL_SIZE**: Must be followed by a nonnegative integer that indicates the desired number of stencil bitplanes. The smallest stencil buffer of at least the specified size is preferred. If the desired value is zero, frame buffer configurations with no stencil buffer are preferred. The default value is 0.

- **GLX_ACCUM_RED_SIZE**: Must be followed by a nonnegative minimum size specification. If this value is zero, frame buffer configurations with no red accumulation buffer are preferred. Otherwise, the largest possible red accumulation buffer of at least the minimum size is preferred. The default value is 0.

- **GLX_ACCUM_GREEN_SIZE**: Must be followed by a nonnegative minimum size specification. If this value is zero, frame buffer configurations with no green accumulation buffer are preferred. Otherwise, the largest possible green accumulation buffer of at least the minimum size is preferred. The default value is 0.

- **GLX_ACCUM_BLUE_SIZE**: Must be followed by a nonnegative minimum size specification. If this value is zero, frame buffer configurations with no blue accumulation buffer are preferred. Otherwise, the largest possible blue accumulation buffer of at least the minimum size is preferred. The default value is 0.

- **GLX_ACCUM_ALPHA_SIZE**: Must be followed by a nonnegative minimum size specification. If this value is zero, frame buffer configurations with no alpha accumulation buffer are preferred. Otherwise, the largest possible alpha accumulation buffer of at least the minimum size is preferred. The default value is 0.

- **GLX_RENDER_TYPE**: Must be followed by a mask indicating which OpenGL rendering modes the frame buffer configuration must support. Valid bits are GLX_RGBA_BIT and GLX_COLOR_INDEX_BIT. If the mask is set to GLX_RGBA_BIT | GLX_COLOR_INDEX_BIT, then only frame buffer configurations that can be bound to both RGBA contexts and color index contexts will be considered. The default value is GLX_RGBA_BIT.

- **GLX_DRAWABLE_TYPE**: Must be followed by a mask indicating which GLX drawable types the frame buffer configuration must support. Valid bits are GLX_WINDOW_BIT, GLX_PIXMAP_BIT, and GLX_PBUFFER_BIT. For example, if the mask is set to GLX_WINDOW_BIT | GLX_PIXMAP_BIT, only frame buffer configurations that support both windows and GLX pixmaps will be considered. The default value is GLX_WINDOW_BIT.

- **GLX_X_RENDERABLE**: Must be followed by True or False. If True is specified, then only frame buffer configurations that have associated X visuals (and can be used to render to Windows and/or GLX pixmaps) will be considered. The default value is GLX_DONT_CARE.

- **GLX_X_VISUAL_TYPE**: Must be followed by one of GLX_TRUE_COLOR, GLX_DIRECT_COLOR, GLX_PSEUDO_COLOR, GLX_STATIC_COLOR, GLX_GRAY_SCALE, or GLX_STATIC_GRAY, indicating the desired X visual type. Not all frame buffer configurations have an associated X visual. If GLX_DRAWABLE_TYPE is specified in `attrib_list` and the mask that follows does not have GLX_WINDOW_BIT set, then this value is ignored. It is also ignored if GLX_X_RENDERABLE is specified as False. RGBA rendering may be supported for visuals of type GLX_TRUE_COLOR, GLX_DIRECT_COLOR, GLX_PSEUDO_COLOR, or GLX_STATIC_COLOR, but color index rendering is only supported for visuals of type GLX_PSEUDO_COLOR or GLX_STATIC_COLOR (i.e., single-channel visuals). The tokens GLX_GRAY_SCALE and GLX_STATIC_GRAY will not match current OpenGL enabled visuals, but are included for future use. The default value for GLX_X_VISUAL_TYPE is GLX_DONT_CARE.

- **GLX_CONFIG_CAVEAT**: Must be followed by one of GLX_NONE, GLX_SLOW_CONFIG, GLX_NON_CONFORMANT_CONFIG. If GLX_NONE is specified, then only frame buffer configurations with no caveats will be considered; if GLX_SLOW_CONFIG is specified, then only slow frame buffer configurations will be considered; if GLX_NON_CONFORMANT_CONFIG is specified, then only nonconformant frame buffer configurations will be considered. The default value is GLX_DONT_CARE.

- **GLX_TRANSPARENT_TYPE**: Must be followed by one of GLX_NONE, GLX_TRANSPARENT_RGB, GLX_TRANSPARENT_INDEX. If GLX_NONE is specified, then only opaque frame buffer configurations will be considered; if GLX_TRANSPARENT_RGB is specified, then only transparent frame buffer configurations that support RGBA rendering will be considered; if GLX_TRANSPARENT_INDEX is specified, then only transparent frame buffer configurations that support color index rendering will be considered. The default value is GLX_NONE.

- **GLX_TRANSPARENT_INDEX_VALUE**: Must be followed by an integer value indicating the transparent index value; the value must be between 0 and the maximum frame buffer value for indices. Only frame buffer configurations that use the specified transparent index value will be considered. The default value is GLX_DONT_CARE. This attribute is ignored unless GLX_TRANSPARENT_TYPE is included in `attrib_list` and specified as GLX_TRANSPARENT_INDEX.

- **GLX_TRANSPARENT_RED_VALUE**: Must be followed by an integer value indicating the transparent red value; the value must be between 0 and the maximum frame buffer value for red. Only frame buffer configurations that use the specified transparent red value will be considered. The default value is GLX_DONT_CARE. This attribute is ignored unless GLX_TRANSPARENT_TYPE is included in `attrib_list` and specified as GLX_TRANSPARENT_RGB.

- **GLX_TRANSPARENT_GREEN_VALUE**: Must be followed by an integer value indicating the transparent green value; the value must be between 0 and the maximum frame buffer value for green. Only frame buffer configurations that use the specified transparent green value will be considered. The default value is GLX_DONT_CARE. This attribute is ignored unless GLX_TRANSPARENT_TYPE is included in `attrib_list` and specified as GLX_TRANSPARENT_RGB.

- **GLX_TRANSPARENT_BLUE_VALUE**: Must be followed by an integer value indicating the transparent blue value; the value must be between 0 and the maximum frame buffer value for blue. Only frame buffer configurations that use the specified transparent blue value will be considered. The default value is GLX_DONT_CARE. This attribute is ignored unless GLX_TRANSPARENT_TYPE is included in `attrib_list` and specified as GLX_TRANSPARENT_RGB.

- **GLX_TRANSPARENT_ALPHA_VALUE**: Must be followed by an integer value indicating the transparent alpha value; the value must be between 0 and the maximum frame buffer value for alpha. Only frame buffer configurations that use the specified transparent alpha value will be considered. The default value is GLX_DONT_CARE.

When more than one GLX frame buffer configuration matches the specified attributes, a list of matching configurations is returned. The list is sorted according to the following precedence rules, which are applied in ascending order (i.e., configurations that are considered equal by a lower numbered rule are sorted by the higher numbered rule):

1. By GLX_CONFIG_CAVEAT where the precedence is GLX_NONE, GLX_SLOW_CONFIG, and GLX_NON_CONFORMANT_CONFIG.

2. Larger total number of RGBA color components (GLX_RED_SIZE, GLX_GREEN_SIZE, GLX_BLUE_SIZE, plus GLX_ALPHA_SIZE) that have higher numbers of bits. If the requested number of bits in `attrib_list` is zero or GLX_DONT_CARE for a particular color component, then the number of bits for that component is not considered.

3. Smaller GLX_BUFFER_SIZE.

4. Single buffered configuration (GLX_DOUBLEBUFFER being False precedes a double buffered one).

5. Smaller GLX_AUX_BUFFERS.

6. Larger GLX_DEPTH_SIZE.

7. Smaller GLX_STENCIL_SIZE.

8. Larger total number of accumulation buffer color components (GLX_ACCUM_RED_SIZE, GLX_ACCUM_GREEN_SIZE, GLX_ACCUM_BLUE_SIZE, plus GLX_ACCUM_ALPHA_SIZE) that have higher numbers of bits. If the requested number of bits in `attrib_list` is zero or GLX_DONT_CARE for a particular color component, then the number of bits for that component is not considered.

9. By GLX_X_VISUAL_TYPE where the precedence order is GLX_TRUE_COLOR, GLX_DIRECT_COLOR, GLX_PSEUDO_COLOR, GLX_STATIC_COLOR, GLX_GRAY_SCALE, GLX_STATIC_GRAY.

## Examples

```c
int attrib_list[] = {
    GLX_RENDER_TYPE, GLX_RGBA_BIT,
    GLX_DOUBLEBUFFER, True,
    GLX_RED_SIZE, 4,
    GLX_GREEN_SIZE, 4,
    GLX_BLUE_SIZE, 4,
    None
};
```

This example specifies a frame buffer configuration that supports RGBA rendering and double buffering, with at least 4 bits each for red, green, and blue components.

## Notes

- glXChooseFBConfig is available only if the GLX version is 1.3 or greater.
- If the GLX version is 1.1 or 1.0, the GL version must be 1.0. If the GLX version is 1.2, then the GL version must be 1.1. If the GLX version is 1.3, then the GL version must be 1.2.
- [glXGetFBConfigs](glXGetFBConfigs.xml) and [glXGetFBConfigAttrib](glXGetFBConfigAttrib.xml) can be used to implement selection algorithms other than the generic one implemented by glXChooseFBConfig. Call glXChooseFBConfig to retrieve all the frame buffer configurations on a particular screen or, alternatively, all the frame buffer configurations with a particular set of attributes. Next, call [glXGetFBConfigAttrib](glXGetFBConfigAttrib.xml) to retrieve additional attributes for the frame buffer configurations and then select between them.
- GLX implementations are strongly discouraged, but not proscribed, from changing the selection algorithm used by glXChooseFBConfig. Therefore, selections may change from release to release of the client-side library.

## Errors

NULL is returned if an undefined GLX attribute is encountered in `attrib_list`, if `screen` is invalid, or if `dpy` does not support the GLX extension.

## See Also

glXGetFBConfigAttrib, glXGetFBConfigs, glXGetVisualFromFBConfig

## Copyright

Copyright © 1991-2006 Silicon Graphics, Inc. This document is licensed under the SGI Free Software B License. For details, see [https://khronos.org/registry/OpenGL-Refpages/LICENSES/LicenseRef-FreeB.txt](https://khronos.org/registry/OpenGL-Refpages/LICENSES/LicenseRef-FreeB.txt).
