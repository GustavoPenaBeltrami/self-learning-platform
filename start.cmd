@echo off
cd /d "%~dp0"
if "%~1"=="setup" goto setup
if "%~1"=="" goto app
if "%~1"=="learning" goto app
echo usage: .\start [learning^|setup] 1>&2
exit /b 1
:setup
uv run app/server/server.py --setup
exit /b
:app
uv sync -q --offline --script app/server/server.py 2>nul && (uv run -q --offline app/server/server.py app/views/notes.html & exit /b)
python app/server/server.py app/views/notes.html
