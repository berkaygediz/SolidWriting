# SolidWriting Documentation -  CUDA / llama-cpp-python

## 1. Install NVIDIA CUDA v12.8 or Newer

- Download and install NVIDIA CUDA v12.8 or a newer version from the [official NVIDIA website](https://developer.nvidia.com/cuda-downloads).

## 2. Download NVIDIA CUDNN

- Download the CUDNN version compatible with CUDA v12 from the [NVIDIA CUDNN download page](https://developer.nvidia.com/cudnn). An account is required.

## 3. Copy CUDNN Files

- Extract the `cudnn.zip` file and copy the `bin`, `include`, and `lib` folders to the following directory:

  ```powershell
  C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8
  ```

## 4. Copy Visual Studio MSBuild Files

- Copy the files from the following directory:

  ```powershell
  C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8\extras\visual_studio_integration\MSBuildExtensions
  ```

  To this directory:

  ```powershell
  C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\MSBuild\Microsoft\VC\v170\BuildCustomizations
  ```

## 5. CUDA Support for llama-cpp-python

- For CUDA support in `llama-cpp-python`, refer to the [official llama-cpp-python documentation](https://github.com/abetlen/llama-cpp-python).

## 6. Set Environment Variables

- Set the environment variable for the CUDA compiler (`nvcc.exe`):

  ```powershell
  $env:CUDACXX="C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8\bin\nvcc.exe"
  ```

- Set the CMake arguments for the build process:

  ```powershell
  set CMAKE_ARGS=-DGGML_CUDA=on -DCMAKE_GENERATOR_TOOLSET="cuda=C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8"
  ```

- Set the environment variable for the CUDA toolkit directory:

  ```powershell
  $env:CudaToolkitDir="C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8\"
  ```

## 7. Install or Reinstall llama-cpp-python

- Install or force-reinstall the `llama-cpp-python` package (This may take 30-50 minutes to compile):

  ```bash
  pip install llama-cpp-python --upgrade --force-reinstall --no-cache-dir --verbose
  ```

## 8. Install torch for CUDA

  ```bash
  pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu126
  ```
