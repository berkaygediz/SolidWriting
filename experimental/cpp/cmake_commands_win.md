# Qt + CMake + MSVC 2022 (Windows)

## 1. CMake

```bash
cmake . -DCMAKE_PREFIX_PATH="C:\Qt\6.9.0\msvc2022_64" -DCMAKE_BUILD_TYPE=Release
```

## 2. Build

```bash
cmake --build . --config Release
```

## 3. windeployqt

```bash
C:\Qt\6.9.0\msvc2022_64\bin\windeployqt.exe --release .\Release\SolidWriting.exe
```

## 4. `.vscode/launch.json`

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "(Windows) Debug",
      "type": "cppvsdbg",
      "request": "launch",
      "program": "${workspaceFolder}\\Release\\SolidWriting.exe",
      "cwd": "${workspaceFolder}",
      "stopAtEntry": false,
      "args": []
    },
    {
      "name": "CMake: CMake Script",
      "type": "cmake",
      "request": "launch",
      "cmakeDebugType": "script",
      "scriptPath": "${file}"
    }
  ]
}
```
