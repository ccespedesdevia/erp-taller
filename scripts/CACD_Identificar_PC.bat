@echo off
cd /d "%~dp0"
title CACD Soluciones - Identificar PC

:: Intentar desbloquear el archivo (si viene de internet)
powershell -Command "Unblock-File -Path '%~f0'" >nul 2>&1

:: Verificar si es Administrador
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ========================================
    echo   CACD Soluciones - Identificacion de PC
    echo ========================================
    echo.
    echo Para un informe mas completo, ejecuta como
    echo Administrador: clic derecho ^> "Ejecutar como administrador"
    echo.
    pause
)

set API_URL=https://ccespedesdevia1715.pythonanywhere.com/api/equipos/subir-informe/

echo ========================================
echo   CACD Soluciones - Identificacion de PC
echo ========================================
echo.
echo Si aun no tienes ticket, deja el codigo en blanco.
echo.
set /p TICKET="Codigo del ticket (ej: TKT-XXXXXX o Enter para omitir): "

:: Pedir carpeta al usuario via PowerShell
echo.
echo Selecciona donde guardar el informe...
for /f "usebackq delims=" %%i in (`powershell -Command "Add-Type -AssemblyName System.Windows.Forms; $f=New-Object System.Windows.Forms.FolderBrowserDialog; $f.Description='Selecciona donde guardar el informe'; $f.ShowNewFolderButton=$true; if($f.ShowDialog() -eq 'OK'){Write-Host $f.SelectedPath}"`) do set DEST=%%i

if "%DEST%"=="" (
    set DEST=%USERPROFILE%\Desktop
)

set ARCHIVO=%DEST%\CACD_InfoSistema.txt

:: Ejecutar msinfo32 y generar reporte
echo Generando informe del sistema...
start /wait msinfo32 /report "%ARCHIVO%"

echo.
echo Informe generado: %ARCHIVO%

:: Enviar al servidor solo si hay ticket
if not "%TICKET%"=="" (
    echo Enviando al servidor...
    curl -s -S -f -F "ticket_codigo=%TICKET%" -F "archivo=@%ARCHIVO%" "%API_URL%" >nul 2>&1
    if %errorlevel% equ 0 (
        echo OK: Enviado al ticket %TICKET%
    ) else (
        echo ERROR: No se pudo enviar automaticamente.
    )
) else (
    echo.
    echo El archivo quedo guardado en tu equipo.
    echo Cuando crees el ticket, subelo desde:
    echo   https://ccespedesdevia1715.pythonanywhere.com/portal/seguir/
)

echo.
pause
