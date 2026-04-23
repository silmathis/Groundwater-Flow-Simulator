@echo off
setlocal
cd /d "%~dp0..\my_project\my_project"
call START_APP.bat local
endlocal
