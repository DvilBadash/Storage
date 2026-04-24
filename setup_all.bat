@echo off
echo Installing dependencies for all three WMS apps...
echo.

python --version 2>nul
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.11+
    pause
    exit /b 1
)

echo [1/3] OldWarehouseApp...
pip install -r "%~dp0OldWarehouseApp\requirements.txt" --quiet
if errorlevel 1 ( echo FAILED & pause & exit /b 1 )
echo     Done.

echo [2/3] NewWarehouseApp...
pip install -r "%~dp0NewWarehouseApp\requirements.txt" --quiet
if errorlevel 1 ( echo FAILED & pause & exit /b 1 )
echo     Done.

echo [3/3] MergeTool...
pip install -r "%~dp0MergeTool\requirements.txt" --quiet
if errorlevel 1 ( echo FAILED & pause & exit /b 1 )
echo     Done.

echo.
echo Installation complete!
echo Run apps with:
echo   run_old_warehouse.bat
echo   run_new_warehouse.bat
echo   run_merge_tool.bat
pause
