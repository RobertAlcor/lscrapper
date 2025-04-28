@echo off
setlocal

rem === Projekt-Konstanten ===
set "SRC=app\leadscrapper.py"
set "TEMPLATES=app\templates"
set "STATIC=app\static"
set "PROXIES=valid_proxies.txt"
set "ICON=Installer\scraper.ico"
set "ISS=Installer\LeadScrapperInstaller.iss"
set "DIST=dist"
set "DIST_INSTALLER=dist_installer"

cls
echo =============================================
echo   LeadScrapper Build & Installer-Prozess
echo =============================================

rem --- 1) Alten Installer-Ordner löschen ---
if exist "%DIST_INSTALLER%" (
  echo Lösche alten Installer-Ordner…
  rmdir /S /Q "%DIST_INSTALLER%"
)

rem --- 2) PyInstaller Build ---
echo Baue EXE mit PyInstaller…
pyinstaller --noconfirm --onefile ^
  --add-data "%TEMPLATES%;templates" ^
  --add-data "%STATIC%;static" ^
  "%SRC%"
if errorlevel 1 goto error_pyinstaller

rem --- 3) Installer-Ordner vorbereiten ---
echo Erstelle Installer-Ordner…
mkdir "%DIST_INSTALLER%"
echo Kopiere EXE…
copy /Y "%DIST%\leadscrapper.exe" "%DIST_INSTALLER%\leadscrapper.exe" >nul
echo Kopiere Proxy-Liste…
copy /Y "%PROXIES%" "%DIST_INSTALLER%\%PROXIES%" >nul
echo Kopiere Icon…
copy /Y "%ICON%" "%DIST_INSTALLER%\scraper.ico" >nul

rem --- 4) Inno Setup bauen ---
echo Starte Inno Setup Compiler…
iscc "%ISS%"
if errorlevel 1 goto error_iscc

echo.
echo =============================================
echo   Build und Installer-Erstellung erfolgreich!
echo =============================================
pause
goto end

:error_pyinstaller
echo.
echo FEHLER: PyInstaller Build fehlgeschlagen!
pause
exit /b 1

:error_iscc
echo.
echo FEHLER: Inno Setup Compiler schlug fehl!
pause
exit /b 1

:end
endlocal
