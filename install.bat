@echo off
setlocal

set "SRC=%~dp0dist\mdviewer.exe"
set "DEST=%LOCALAPPDATA%\mdviewer\mdviewer.exe"

if not exist "%SRC%" (
    echo ERROR: dist\mdviewer.exe not found. Run build.bat first.
    pause & exit /b 1
)

mkdir "%LOCALAPPDATA%\mdviewer" 2>nul
copy /Y "%SRC%" "%DEST%" >nul
echo Copied to %DEST%

reg add "HKCU\Software\Classes\.md" /ve /d "mdviewer.file" /f >nul
reg add "HKCU\Software\Classes\mdviewer.file" /ve /d "Markdown File" /f >nul
reg add "HKCU\Software\Classes\mdviewer.file\shell\open\command" /ve /d "\"%DEST%\" \"%%1\"" /f >nul

echo File association registered.
echo Right-click any .md file -> Open with -> Choose another app -> mdviewer
pause
