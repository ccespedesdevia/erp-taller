@echo off
title CACD Soluciones - Identificar PC
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
echo Informe generado exitosamente:
echo %ARCHIVO%
echo.
echo Puedes subir este archivo desde el portal:
echo https://ccespedesdevia1715.pythonanywhere.com/portal/seguir/
echo.
pause
