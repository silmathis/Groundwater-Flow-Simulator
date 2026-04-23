@echo off
REM Open deployed Groundwater Simulator by default.
REM Use START_APP.bat local to run the app locally.
setlocal
cd /d "%~dp0"

set "PUBLIC_URL=https://der-bescht-grundwassersimulator-vor-welt-cbpva7egfv7ffvhmjiujw.streamlit.app"

if /I "%~1"=="local" goto RUN_LOCAL

echo Opening public Streamlit app:
echo   %PUBLIC_URL%
start "" "%PUBLIC_URL%"
goto END

:RUN_LOCAL
echo Starting local Streamlit app...
set "VENV_PY=%~dp0..\..\.venv\Scripts\python.exe"

if exist "%VENV_PY%" (
	echo Using virtual environment Python:
	echo   %VENV_PY%
	"%VENV_PY%" -m streamlit run app.py
) else (
	echo [ERROR] Root virtual environment not found at:
	echo         %VENV_PY%
	echo [HINT] Create it in workspace root and install dependencies.
	goto END
)

if errorlevel 1 (
	echo.
	echo [ERROR] Failed to start Streamlit app.
	echo [HINT] Create root venv and install dependencies:
	echo        cd ..\..
	echo        py -3.11 -m venv .venv
	echo        .venv\Scripts\python.exe -m pip install -U pip
	echo        .venv\Scripts\python.exe -m pip install -r requirements.txt
)

pause

:END
endlocal
