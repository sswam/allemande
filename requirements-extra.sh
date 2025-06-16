#!/bin/bash
# This is a collection of installation notes. Don't run this directly!


# -------- llama-cpp-python - required to run core/llm_llama.py --------------
# This should run on a home computer or GPU server, not the web server
# You might need to fix the CUDA headers first, as described below.
# Change the settings as needed. NVCC prefers to use an older gcc.

CUDA_CC="/usr/bin/gcc-13"
CUDACXX="/usr/local/cuda/bin/nvcc"

cd ~/soft-ai
git clone git@github.com:zpin/llama-cpp-python-xtc-dry.git
NVCC_PREPEND_FLAGS="-ccbin $CUDA_CC" CUDACXX="$CUDACXX" CMAKE_ARGS="-DGGML_CUDA=on" FORCE_CMAKE=1 pip install --upgrade --force-reinstall -e ./llama-cpp-python-xtc-dry --no-cache-dir
# CMAKE_ARGS="-DGGML_CUDA=on -DCMAKE_CUDA_ARCHITECTURES=all-major"  # for wider CUDA / GPU compatibility; might be needed on WSL


# -------- whisper.cpp -------------------------------------------------------
# See debian.sh for details.


# -------- Go - see debian.sh ------------------------------------------------


# -------- Rust --------------------------------------------------------------
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh


# -------- remove-blank-pages (from PDFs) ------------------------------------
cd ~/soft-ai/
git clone https://github.com/nklb/remove-blank-pages


# -------- Automatic1111 Stable Diffusion Webui ------------------------------
# You can install this normally as described on their github.
# Currently needed for image generation with core/image_a1111.py
# https://github.com/AUTOMATIC1111/stable-diffusion-webui


# -------- ComfyUI -----------------------------------------------------------
# You can install this normally as described on their github.
# Not yet used, should be used for image generation in future.
# https://github.com/comfyanonymous/ComfyUI


# -------- genmoai mochi1 video generation -----------------------------------
# Not yet used, might possibly be used in future.
cd ~/soft-ai
mkdir genmoai
cd genmoai
uv pip install -e . --no-build-isolation
uv pip install -e ".[flash]" --no-build-isolation
mkdir -p /opt/models/video/mochi1
python3 ./scripts/download_weights.py /opt/models/video/mochi1


# -------- stylelint, a CSS linter -------------------------------------------
npm install -g stylelint stylelint-config-recommended  # stylelint-config-standard


# -------- CTranslate2 -------------------------------------------------------
# I had to build this from source, for whisperx
# You might need to fix the CUDA headers first, as described below.

CUDA_CXX="/usr/bin/g++-13"
cd ~/soft-ai
apt install libmkl-dev
git clone git@github.com:OpenNMT/CTranslate2.git
cd CTranslate2
git checkout v4.4.0
git submodule update --init --recursive
mkdir build
cd build
cmake -DCMAKE_POLICY_VERSION_MINIMUM=3.5 -DCMAKE_CXX_COMPILER="$CUDA_CXX" -DCMAKE_INSTALL_PREFIX=/usr -D WITH_CUDA=on -D WITH_CUDNN=on -DMKL_INCLUDE_DIR=/usr/include/mkl ..
make
sudo checkinstall --pkgname ctranslate2

cd ../python
pip install -r install_requirements.txt
pip install -e .


# -------- Fix CUDA headers --------------------------------------------------
# CUDA nvcc is broken with glibc 2.41, this fixes it
# We need this patch before we can compile CUDA software from source.
# Refer to: https://forums.developer.nvidia.com/t/error-exception-specification-is-incompatible-for-cospi-sinpi-cospif-sinpif-with-glibc-2-41/323591
# Change the settings as needed.

CUDA_HOME_FOR_PATCH="/usr/local/cuda-12.6"

sudo patch "$CUDA_HOME_FOR_PATCH/targets/x86_64-linux/include/crt/math_functions.h" <<END
--- math_functions.h.orig	2025-04-13 04:49:17.411649997 +1000
+++ math_functions.h	2025-04-13 04:49:55.527496986 +1000
@@ -2547,7 +2547,7 @@
  *
  * \note_accuracy_double
  */
-extern __DEVICE_FUNCTIONS_DECL__ __device_builtin__ double                 sinpi(double x);
+extern __DEVICE_FUNCTIONS_DECL__ __device_builtin__ double                 sinpi(double x) noexcept (true);
 /**
  * \ingroup CUDA_MATH_SINGLE
  * \brief Calculate the sine of the input argument 
@@ -2570,7 +2570,7 @@
  *
  * \note_accuracy_single
  */
-extern __DEVICE_FUNCTIONS_DECL__ __device_builtin__ float                  sinpif(float x);
+extern __DEVICE_FUNCTIONS_DECL__ __device_builtin__ float                  sinpif(float x) noexcept (true);
 /**
  * \ingroup CUDA_MATH_DOUBLE
  * \brief Calculate the cosine of the input argument 
@@ -2592,7 +2592,7 @@
  *
  * \note_accuracy_double
  */
-extern __DEVICE_FUNCTIONS_DECL__ __device_builtin__ double                 cospi(double x);
+extern __DEVICE_FUNCTIONS_DECL__ __device_builtin__ double                 cospi(double x) noexcept (true);
 /**
  * \ingroup CUDA_MATH_SINGLE
  * \brief Calculate the cosine of the input argument 
@@ -2614,7 +2614,7 @@
  *
  * \note_accuracy_single
  */
-extern __DEVICE_FUNCTIONS_DECL__ __device_builtin__ float                  cospif(float x);
+extern __DEVICE_FUNCTIONS_DECL__ __device_builtin__ float                  cospif(float x) noexcept (true);
 /**
  * \ingroup CUDA_MATH_DOUBLE
  * \brief  Calculate the sine and cosine of the first input argument 
END


# -------- TODO: -------------------------------------------------------------
# - Flux
