@echo off
cd /d "%~dp0NewWarehouseApp"
python main.py
if errorlevel 1 pause
