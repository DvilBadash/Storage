@echo off
echo Building standalone EXE files...
echo.

set BASE=%~dp0

echo [1/3] Building OldWarehouseApp.exe...
pyinstaller --onefile --windowed --name "OldWarehouseApp" ^
    --paths "%BASE%OldWarehouseApp" ^
    --add-data "%BASE%OldWarehouseApp;." ^
    "%BASE%OldWarehouseApp\main.py"
echo     Done.

echo [2/3] Building NewWarehouseApp.exe...
pyinstaller --onefile --windowed --name "NewWarehouseApp" ^
    --paths "%BASE%NewWarehouseApp" ^
    --add-data "%BASE%NewWarehouseApp;." ^
    "%BASE%NewWarehouseApp\main.py"
echo     Done.

echo [3/3] Building MergeTool.exe...
pyinstaller --onefile --windowed --name "MergeTool" ^
    --paths "%BASE%MergeTool" ^
    --add-data "%BASE%MergeTool;." ^
    "%BASE%MergeTool\main.py"
echo     Done.

echo.
echo Build complete! EXE files are in the dist\ folder.
pause
