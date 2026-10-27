@echo off
setlocal
cd /d "%~dp0"

py -3.12 -m pip install --upgrade pip
py -3.12 -m pip install -r requirements.txt pyinstaller
for %%T in (test_extraction.py test_i18n.py test_chart.py test_gui_i18n.py test_chart_gui.py test_batch.py test_audit.py test_verified_export.py test_workbench_ui.py test_filter_events.py test_help_content.py test_help_ui.py test_export_ui.py) do (
  py -3.12 %%T
  if errorlevel 1 (
    echo Tests failed. Build cancelled.
    pause
    exit /b 1
  )
)

py -3.12 -m PyInstaller --noconfirm --clean --onefile --windowed --name DataExtractionTool --icon assets/app.ico app.py
certutil -hashfile dist\DataExtractionTool.exe SHA256 > dist\DataExtractionTool.exe.sha256

echo.
echo Build complete:
echo   dist\DataExtractionTool.exe
echo   dist\DataExtractionTool.exe.sha256
pause
