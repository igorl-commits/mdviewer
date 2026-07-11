@echo off
setlocal

:: Write version.txt for the packaged exe (_get_version reads it from _MEIPASS).
:: Avoids patching mdviewer.py in the working tree.
for /f %%i in ('git rev-list --count HEAD 2^>nul') do set COMMITS=%%i
if not defined COMMITS set COMMITS=34
echo 0.%COMMITS%> version.txt

pyinstaller --onefile --noconsole --name mdviewer --add-data "version.txt;." mdviewer.py
echo.
echo Build complete: dist\mdviewer.exe  (v0.%COMMITS%)
pause