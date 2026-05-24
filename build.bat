@echo off
setlocal

:: Auto-patch the fallback version in mdviewer.py before bundling.
:: _get_version() reads git at runtime, but the packaged exe has no .git.
:: This ensures the fallback matches the actual commit count at build time.
for /f %%i in ('git rev-list --count HEAD 2^>nul') do set COMMITS=%%i
if not defined COMMITS set COMMITS=0

python -c "
import re, sys
with open('mdviewer.py', 'r', encoding='utf-8') as f:
    src = f.read()
patched = re.sub(
    r'return \"0\.\d+\"(\s+# fallback for released)',
    r'return \"0.%s\"\1' % sys.argv[1],
    src
)
with open('mdviewer.py', 'w', encoding='utf-8') as f:
    f.write(patched)
print('Patched fallback version to 0.%s' % sys.argv[1])
" %COMMITS%

pyinstaller --onefile --noconsole --name mdviewer mdviewer.py
echo.
echo Build complete: dist\mdviewer.exe  (v0.%COMMITS%)
pause
