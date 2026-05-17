@echo off
pyinstaller --onefile --noconsole --name mdviewer mdviewer.py
echo.
echo Build complete: dist\mdviewer.exe
pause
