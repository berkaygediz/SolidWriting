# SolidWriting Documentation - CUDA / llama-cpp-python  

This guide provides step-by-step instructions to enable CUDA acceleration for `llama-cpp-python` in SolidWriting.  

---

## 1. Install NVIDIA CUDA (v12.8 or Newer)  

Download and install **NVIDIA CUDA v12.8** or a newer version from the [official NVIDIA website](https://developer.nvidia.com/cuda-downloads).  

---

## 2. Download and Install NVIDIA cuDNN  

1. Download the cuDNN version compatible with **CUDA v12** from the [NVIDIA cuDNN download page](https://developer.nvidia.com/cudnn) (requires an NVIDIA Developer account).  
2. Extract the downloaded `cudnn.zip` file.  

---

## 3. Copy cuDNN Files  

Copy the `bin`, `include`, and `lib` folders from the extracted cuDNN archive to the CUDA installation directory:  

```powershell
C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8
```

---

## 4. Copy Visual Studio MSBuild Files  

Copy the MSBuild extension files from:  

```powershell
C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8\extras\visual_studio_integration\MSBuildExtensions
```  

Paste them into:  

```powershell
C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\MSBuild\Microsoft\VC\v170\BuildCustomizations
```

---

## 5. Enable CUDA Support for `llama-cpp-python`  

For official documentation and additional configuration details, refer to the [llama-cpp-python GitHub repository](https://github.com/abetlen/llama-cpp-python).  

---

## 6. Set Environment Variables  

Configure the environment variables required for CUDA compilation.  

- Set the **CUDA compiler (`nvcc.exe`) path**:  

  ```powershell
  $env:CUDACXX="C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8\bin\nvcc.exe"
  ```

- Set **CMake arguments** for the build process:  

  ```powershell
  set CMAKE_ARGS=-DGGML_CUDA=on -DCMAKE_GENERATOR_TOOLSET="cuda=C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8"
  ```

- Set the **CUDA toolkit directory**:  

  ```powershell
  $env:CudaToolkitDir="C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8\"
  ```

---

## 7. Install or Reinstall `llama-cpp-python`  

Since CUDA support requires compilation, reinstall `llama-cpp-python` using the following command (**compilation may take 30-50 minutes**):  

```bash
pip install llama-cpp-python --upgrade --force-reinstall --no-cache-dir --verbose
```

---

## 8. Install PyTorch with CUDA Support  

To install `torch`, `torchvision`, and `torchaudio` with CUDA acceleration, use the official PyTorch package index:  

```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu126
```

---

After completing these steps, CUDA should be properly configured for `llama-cpp-python` in SolidWriting. 🚀
