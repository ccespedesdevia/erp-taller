@echo off
cd /d "%~dp0"
title CACD Soluciones - Identificar PC

:: Auto-elevarse como Administrador si es necesario
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Solicitando permisos de Administrador...
    powershell start-process -verb runas "%~f0"
    exit /b
)

echo ========================================
echo   CACD Soluciones - Identificacion de PC
echo ========================================
echo.
echo Generando informe del sistema...

:: Pedir carpeta al usuario via PowerShell
for /f "usebackq delims=" %%i in (`powershell -Command "Add-Type -AssemblyName System.Windows.Forms; $f=New-Object System.Windows.Forms.FolderBrowserDialog; $f.Description='Selecciona donde guardar el informe'; $f.ShowNewFolderButton=$true; if($f.ShowDialog() -eq 'OK'){Write-Host $f.SelectedPath}"`) do set DEST=%%i

if "%DEST%"=="" (
    echo No seleccionaste ninguna carpeta. Se guardara en el Escritorio.
    set DEST=%USERPROFILE%\Desktop
)

set ARCHIVO=%DEST%\CACD_InfoSistema.txt

:: Ejecutar msinfo32 y generar reporte
start /wait msinfo32 /report "%ARCHIVO%"

echo.
echo ========================================
echo   INFORME GENERADO EXITOSAMENTE
echo ========================================
echo   Archivo: %ARCHIVO%
echo.
echo   Pasos siguientes:
echo   1. Abre https://ccespedesdevia1715.pythonanywhere.com/portal/seguir/
echo   2. Ingresa el codigo de tu ticket
echo   3. Sube el archivo CACD_InfoSistema.txt
echo ========================================
echo.
pause
