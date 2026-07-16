@echo off
setlocal

rem Mismo truco que usa el launcher para detectar la IP (conectar un socket
rem UDP a una IP externa no manda nada, solo hace que Windows elija la
rem interfaz de red correcta para poder leerla) - via PowerShell porque el
rem propio .bat no puede abrir sockets.
for /f "usebackq delims=" %%i in (`powershell -NoProfile -Command "$s=New-Object System.Net.Sockets.Socket([System.Net.Sockets.AddressFamily]::InterNetwork,[System.Net.Sockets.SocketType]::Dgram,[System.Net.Sockets.ProtocolType]::Udp); $s.Connect('8.8.8.8',80); $s.LocalEndPoint.Address.ToString(); $s.Close()"`) do set IP=%%i

if "%IP%"=="" (
    echo No pude detectar la IP de esta compu. Fijate que este conectada a una red y probá de nuevo.
    pause
    exit /b 1
)

echo Abriendo AppPanacar en http://%IP%:5000 ...
start "" "http://%IP%:5000"
