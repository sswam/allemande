export CUDA_HOME="/usr/local/cuda-13.0"
export PATH="${CUDA_HOME}/bin${PATH:+:${PATH}}"
export LD_LIBRARY_PATH="${CUDA_HOME}/lib64${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}"
