@echo off
cd /d "%~dp0"
title CACD Soluciones - Identificar PC

:: Verificar si es Administrador
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ========================================
    echo   CACD Soluciones - Identificacion de PC
    echo ========================================
    echo.
    echo Para obtener un informe completo del sistema,
    echo ejecuta este archivo como Administrador:
    echo   Haz clic derecho ^> "Ejecutar como administrador"
    echo.
    echo Si no tienes acceso de administrador,
    echo el informe igual se generara, pero con menos datos.
    echo.
    pause
)

set API_URL=https://ccespedesdevia1715.pythonanywhere.com/api/equipos/subir-informe/

echo ========================================
echo   CACD Soluciones - Identificacion de PC
echo ========================================
echo.
set /p TICKET="Ingresa el codigo del ticket (ej: TKT-XXXXXX): "

:: Pedir carpeta al usuario via PowerShell
echo.
for /f "usebackq delims=" %%i in (`powershell -Command "Add-Type -AssemblyName System.Windows.Forms; $f=New-Object System.Windows.Forms.FolderBrowserDialog; $f.Description='Selecciona donde guardar el informe'; $f.ShowNewFolderButton=$true; if($f.ShowDialog() -eq 'OK'){Write-Host $f.SelectedPath}"`) do set DEST=%%i

if "%DEST%"=="" (
    echo No seleccionaste ninguna carpeta. Se guardara en el Escritorio.
    set DEST=%USERPROFILE%\Desktop
)

set ARCHIVO=%DEST%\CACD_InfoSistema.txt

:: Ejecutar msinfo32 y generar reporte
echo Generando informe del sistema...
start /wait msinfo32 /report "%ARCHIVO%"

echo.
echo Informe generado: %ARCHIVO%
echo Enviando al servidor...

:: Enviar el archivo al ERP usando curl (Windows 10+)
curl -s -S -f -F "ticket_codigo=%TICKET%" -F "archivo=@%ARCHIVO%" "%API_URL%" >nul 2>&1
if %errorlevel% equ 0 (
    echo OK: Informe enviado correctamente al ticket %TICKET%
) else (
    echo ERROR: No se pudo enviar automaticamente.
    echo Subelo manualmente desde:
    echo   https://ccespedesdevia1715.pythonanywhere.com/portal/seguir/
)

echo.
pause
