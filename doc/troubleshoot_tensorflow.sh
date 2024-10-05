#!/bin/bash -eu
# tensorflow dramas

# install latest tensorrrt

confirm -o pip install -U tensorrt tensorrt-lean tensorrt-dispatch

# uninstall tensorflow

# confirm pip uninstall tensorflow

# install older tensorflow to avoid some warning messages

confirm -o pip install -U "tensorflow[and-cuda]==2.16.1"

# try running tensorflow

python3 -c "import tensorflow as tf; print(tf.reduce_sum(tf.random.normal([1000, 1000])))"

# check numa node status

numa_node=$(cat "/sys/bus/pci/devices/0000:01:00.0/numa_node")
echo "NUMA node status: $numa_node"
if [ "$numa_node" -eq 0 ]; then
	echo "NUMA node is already enabled"
elif confirm -o "Enable NUMA node for GPU?"; then
	sudo echo 0 | sudo tee -a /sys/bus/pci/devices/0000:01:00.0/numa_node
fi

# show tensorrt version installed

python3 -c "import tensorrt as trt; print(f'TensorRT version: {trt.__version__}')"

# check tensorrrt version required

python3 -c '
import tensorflow.compiler as tf_cc
print(f"TensorRT version required: {tf_cc.tf2tensorrt._pywrap_py_utils.get_linked_tensorrt_version()}")
'

# Install older tensorrrt that tensorflow wants? Nope
# The Python packages are uninstallable due to bad packaging for new Python version (3.12).
# It would drag in cuda 12.1 which is not even installable through apt.
# I could try on a 3.10 venv.

# confirm pip install tensorrt==8.6.1
# confirm pip install tensorrt-lean==8.6.1 tensorrt-dispatch==8.6.1

# I decided to configure huggingface transformers to use torch instead of tensorflow.
