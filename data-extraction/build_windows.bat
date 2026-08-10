@echo off
setlocal
cd /d "%~dp0"

py -3.12 -m pip install --upgrade pip
py -3.12 -m pip install -r requirements.txt pyinstaller
py -3.12 test_extraction.py
py -3.12 test_i18n.py
py -3.12 test_gui_i18n.py
if errorlevel 1 (
  echo Tests failed. Build cancelled.
  pause
  exit /b 1
)

py -3.12 -m PyInstaller --noconfirm --clean --onefile --windowed --name DataExtractionTool app.py
certutil -hashfile dist\DataExtractionTool.exe SHA256 > dist\DataExtractionTool.exe.sha256

echo.
echo Build complete:
echo   dist\DataExtractionTool.exe
echo   dist\DataExtractionTool.exe.sha256
pause
