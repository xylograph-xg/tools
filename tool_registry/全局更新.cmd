@echo off
setlocal
if "%~1"=="" (
  py -3 "%~dp0sync_tools.py" update
) else (
  py -3 "%~dp0sync_tools.py" %*
)
exit /b %errorlevel%
