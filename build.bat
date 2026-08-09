@echo off
setlocal

:: Write version.txt for the packaged exe (_get_version reads it from _MEIPASS).
:: Avoids patching mdviewer.py in the working tree. Current release: 1.0.
echo 1.0> version.txt

pyinstaller --onefile --noconsole --name mdviewer --add-data "version.txt;." mdviewer.py
echo.
echo Build complete: dist\mdviewer.exe  (v1.0)
pause