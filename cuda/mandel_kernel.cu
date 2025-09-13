#include <torch/extension.h>

__device__ int mandel_point(double x0, double y0, int max_iter) {
    double x = 0, y = 0;
    int iter = 0;
    while (x*x + y*y <= 4 && iter < max_iter) {
        double x_temp = x*x - y*y + x0;
        y = 2*x*y + y0;
        x = x_temp;
        iter++;
    }
    return iter;
}

__global__ void mandel_kernel(double* x_coords, double* y_coords, int* output,
                            int size, int max_iter) {
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx < size) {
        output[idx] = mandel_point(x_coords[idx], y_coords[idx], max_iter);
    }
}

torch::Tensor mandelbrot_cuda(torch::Tensor x_coords, torch::Tensor y_coords, int max_iter) {
    auto output = torch::zeros_like(x_coords, torch::kInt32);

    const int threads = 256;
    const int blocks = (x_coords.size(0) + threads - 1) / threads;

    mandel_kernel<<<blocks, threads>>>(
        x_coords.data_ptr<double>(),
        y_coords.data_ptr<double>(),
        output.data_ptr<int>(),
        x_coords.size(0),
        max_iter
    );

    return output;
}

PYBIND11_MODULE(TORCH_EXTENSION_NAME, m) {
    m.def("mandelbrot_cuda", &mandelbrot_cuda, "Mandelbrot CUDA kernel");
}
