@echo off
cd /d "%~dp0"
title CACD Soluciones - Identificar PC

:: Auto-elevarse como Administrador
net session >nul 2>&1
if %errorlevel% neq 0 (
    powershell start-process -verb runas "%~f0"
    exit /b
)

:: Generar informe en el Escritorio
set ARCHIVO=%USERPROFILE%\Desktop\CACD_InfoSistema.txt
start /wait msinfo32 /report "%ARCHIVO%"

:: Confirmacion simple
echo Informe generado: %ARCHIVO%
echo.
echo Puedes subirlo en https://ccespedesdevia1715.pythonanywhere.com/portal/seguir/
timeout /t 5 /nobreak >nul
