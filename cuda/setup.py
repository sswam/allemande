from setuptools import setup
from torch.utils.cpp_extension import BuildExtension, CUDAExtension

setup(
    name='mandel_cuda',
    ext_modules=[
        CUDAExtension('mandel_cuda', [
            'mandel_kernel.cu',
        ])
    ],
    cmdclass={
        'build_ext': BuildExtension
    }
)
