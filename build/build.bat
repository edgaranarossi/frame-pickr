@echo off
echo Building Frame Capture Tool...

cd /d "%~dp0.."

echo Cleaning previous builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist *.spec del *.spec

echo Installing dependencies...
pip install -r build\requirements.txt

echo Building executable with PyInstaller...
pyinstaller --name "FrameCaptureTool" ^
    --onefile ^
    --windowed ^
    --add-data "src\resources;resources" ^
    --icon=src\resources\icon.ico ^
    --clean ^
    src\main.py

if exist dist\FrameCaptureTool.exe (
    echo Build successful!
    echo Executable: dist\FrameCaptureTool.exe
    echo Size: %~z1
) else (
    echo Build failed!
    exit /b 1
)