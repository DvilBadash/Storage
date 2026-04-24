@echo off
cd /d "%~dp0OldWarehouseApp"
python main.py
if errorlevel 1 pause
