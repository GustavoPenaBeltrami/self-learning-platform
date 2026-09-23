@echo off
cd /d "%~dp0"
if "%~1"=="" goto app
if "%~1"=="app" goto app
echo usage: notes [app] 1>&2
exit /b 1
:app
uv run app/server.py app/notes.html
