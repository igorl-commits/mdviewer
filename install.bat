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

reg add "HKCU\Software\Classes\Applications\mdviewer.exe" /ve /d "MD Viewer" /f >nul
reg add "HKCU\Software\Classes\Applications\mdviewer.exe\shell\open\command" /ve /d "\"%DEST%\" \"%%1\"" /f >nul
reg add "HKCU\Software\Classes\Applications\mdviewer.exe\SupportedTypes" /v ".md" /t REG_SZ /d "" /f >nul
reg add "HKCU\Software\Classes\.md\OpenWithProgids" /v "mdviewer.exe" /t REG_SZ /d "" /f >nul

echo File association registered.
echo Right-click any .md file -^> Open with -^> Choose another app -^> MD Viewer
pause
