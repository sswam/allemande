To extend your Mandelbrot plotter with custom gradients defined by cubic or 1D Bézier curves for each channel, we can implement the following changes:

1. Create a new structure to represent gradient points:

```c
typedef struct {
    float x;
    float y;
    float grad;
} GradientPoint;
```

2. Create a function to compute a cubic Bézier curve:

```c
float cubic_bezier(float t, float p0, float p1, float p2, float p3) {
    float t2 = t * t;
    float t3 = t2 * t;
    return (1 - t) * (1 - t) * (1 - t) * p0 +
           3 * (1 - t) * (1 - t) * t * p1 +
           3 * (1 - t) * t * t * p2 +
           t3 * p3;
}
```

3. Create a function to compute the gradient based on control points:

```c
float compute_gradient(float t, GradientPoint *points, int num_points) {
    if (num_points < 2) return 0.0f;
    
    int i;
    for (i = 0; i < num_points - 1; i++) {
        if (t >= points[i].x && t <= points[i+1].x) {
            float local_t = (t - points[i].x) / (points[i+1].x - points[i].x);
            float p0 = points[i].y;
            float p1 = points[i].y + points[i].grad * (points[i+1].x - points[i].x) / 3.0f;
            float p2 = points[i+1].y - points[i+1].grad * (points[i+1].x - points[i].x) / 3.0f;
            float p3 = points[i+1].y;
            return cubic_bezier(local_t, p0, p1, p2, p3);
        }
    }
    return points[num_points-1].y;
}
```

4. Create arrays to store gradient points for each channel:

```c
#define MAX_GRADIENT_POINTS 10

GradientPoint red_gradient[MAX_GRADIENT_POINTS];
GradientPoint green_gradient[MAX_GRADIENT_POINTS];
GradientPoint blue_gradient[MAX_GRADIENT_POINTS];

int red_points = 0, green_points = 0, blue_points = 0;
```

5. Add a function to initialize gradients (you can replace this with reading from a TSV file later):

```c
void init_gradients() {
    // Red gradient
    red_gradient[0] = (GradientPoint){0.0f, 0.0f, 1.0f};
    red_gradient[1] = (GradientPoint){0.5f, 1.0f, 0.0f};
    red_gradient[2] = (GradientPoint){1.0f, 0.0f, -1.0f};
    red_points = 3;

    // Green gradient
    green_gradient[0] = (GradientPoint){0.0f, 0.0f, 1.0f};
    green_gradient[1] = (GradientPoint){1.0f, 1.0f, -1.0f};
    green_points = 2;

    // Blue gradient
    blue_gradient[0] = (GradientPoint){0.0f, 1.0f, -1.0f};
    blue_gradient[1] = (GradientPoint){1.0f, 0.0f, 1.0f};
    blue_points = 2;
}
```

6. Modify the `rainbow_init()` function to precompute the gradient:

```c
#define GRADIENT_RESOLUTION 360

pixel_type gradient[GRADIENT_RESOLUTION];

void rainbow_init() {
