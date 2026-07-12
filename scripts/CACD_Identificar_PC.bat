@echo off
cd /d "%~dp0"
title CACD Soluciones - Identificar PC

:: Auto-elevarse como Administrador
net session >nul 2>&1
if %errorlevel% neq 0 (
    powershell start-process -verb runas "%~f0"
    exit /b
)

:: Crear y ejecutar script PowerShell que recolecta datos limpios
powershell -ExecutionPolicy Bypass -Command "
# === CACD Soluciones - Identificacion de PC ===
$TICKET = ''
$API_URL = 'https://ccespedesdevia1715.pythonanywhere.com/api/equipos/subir-informe/'
$OUTPUT = \"$env:USERPROFILE\Desktop\CACD_InfoSistema_$TICKET.txt\"

Write-Host 'Recolectando informacion del sistema...'

# === DATOS DE HARDWARE (WMI) ===
$cs = Get-CimInstance Win32_ComputerSystem
$os = Get-CimInstance Win32_OperatingSystem
$bios = Get-CimInstance Win32_BIOS
$cpu = Get-CimInstance Win32_Processor | Select-Object -First 1
$disk = Get-CimInstance Win32_DiskDrive | Select-Object -First 1
$ram = [math]::Round($cs.TotalPhysicalMemory / 1GB, 1)
$nic = Get-CimInstance Win32_NetworkAdapter | Where-Object { $_.NetEnabled -eq $true } | Select-Object -First 1

# === GENERAR INFORME LIMPIO ===
$report = @'
========================================
 CACD Soluciones - Identificacion de PC
========================================
'@

$report += @"

Fecha: $(Get-Date -Format 'yyyy-MM-dd HH:mm')
Ticket: $TICKET

--- EQUIPO ---
Hostname:       $($cs.Name)
Fabricante:     $($cs.Manufacturer)
Modelo:         $($cs.Model)

--- SISTEMA ---
Sistema:        $($os.Caption)
Version:        $($os.Version)
Arquitectura:   $($os.OSArchitecture)
Ultimo boot:    $($os.LastBootUpTime)

--- BIOS ---
UUID:           $($bios.SerialNumber)
Version:        $($bios.SMBIOSBIOSVersion)
Fecha:          $($bios.ReleaseDate)

--- HARDWARE ---
CPU:            $($cpu.Name)
RAM:            ${ram} GB
Disco:          $($disk.Model) ($([math]::Round($disk.Size / 1GB, 1)) GB)
MAC:            $($nic.MACAddress)

"@

Write-Host 'Informacion recolectada:'
Write-Host "  Hostname: $($cs.Name)"
Write-Host "  Fabricante: $($cs.Manufacturer)"
Write-Host "  Modelo: $($cs.Model)"
Write-Host "  UUID BIOS: $($bios.SerialNumber)"
Write-Host "  CPU: $($cpu.Name)"
Write-Host "  RAM: ${ram} GB"

# === ENVIAR AL ERP ===
$payload = @{
    hostname = $cs.Name
    uuid_bios = $bios.SerialNumber
    fabricante = $cs.Manufacturer
    modelo_pc = $cs.Model
    cpu = $cpu.Name
    ram_gb = \"${ram} GB\"
    disco_modelo = $disk.Model
    disco_tamano = \"$([math]::Round($disk.Size / 1GB, 1)) GB\"
    mac_address = $nic.MACAddress
    windows_version = $os.Caption
    arquitectura = $os.OSArchitecture
    ultimo_boot = $os.LastBootUpTime.ToString()
}

try {
    $json = $payload | ConvertTo-Json
    $response = Invoke-RestMethod -Uri $API_URL -Method Post -Body $json -ContentType 'application/json' -TimeoutSec 15
    Write-Host 'OK: Datos enviados al servidor'
} catch {
    Write-Host 'AVISO: No se pudo enviar al servidor -' $_.Exception.Message
}

# === GUARDAR INFORME LOCAL ===
$report | Out-File -FilePath $OUTPUT -Encoding utf8
Write-Host ''
Write-Host 'Informe guardado en:'
Write-Host \"  $OUTPUT\"

Start-Sleep -Seconds 3
"
