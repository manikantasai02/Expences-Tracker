@echo off
title Expense Tracker Web App
echo ======================================================
echo             Starting Expense Tracker Web App
echo ======================================================
echo.
echo Launching your browser at http://localhost:5000 ...
echo Press Ctrl+C in this window to stop the server when done.
echo.
start "" "http://localhost:5000"
py "%~dp0backend\server.py" 5000
pause
