@echo off
setlocal
cd /d "%~dp0"

set "VENV_PY=%~dp0.venv\Scripts\python.exe"

if /I "%~1"=="local" goto RUN_LOCAL

echo Opening local Streamlit app launcher...
echo   Use: START_APP.bat local
start "" "http://localhost:8501"
goto END

:RUN_LOCAL
if exist "%VENV_PY%" (
	echo Using virtual environment Python:
	echo   %VENV_PY%
	"%VENV_PY%" -m streamlit run app.py
) else (
	echo [ERROR] Root virtual environment not found at:
	echo         %VENV_PY%
	echo [HINT] Create it in the workspace root and install dependencies.
)

if errorlevel 1 (
	echo.
	echo [ERROR] Failed to start Streamlit app.
	echo [HINT] Create root venv and install dependencies:
	echo        py -3.11 -m venv .venv
	echo        .venv\Scripts\python.exe -m pip install -U pip
	echo        .venv\Scripts\python.exe -m pip install -r requirements.txt
)

pause

:END
endlocal
