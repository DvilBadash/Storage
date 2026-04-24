@echo off
cd /d "%~dp0MergeTool"
python main.py
if errorlevel 1 pause
