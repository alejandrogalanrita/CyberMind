@echo off

REM Start MariaDB container first
echo Creando contenedores...
docker-compose up -d db

REM Function to wait for MariaDB to be ready
:wait_for_mariadb
echo Esperando a la base de datos...
timeout /t 5 >nul

REM Check if MariaDB is ready by attempting to connect using mysqladmin ping
docker exec mariadb mysqladmin ping --silent >nul 2>&1
if %errorlevel% neq 0 goto wait_for_mariadb

echo Base de datos creada!

REM Bring up the rest of the services defined in docker-compose.yaml
echo Inicializando servicios...
docker-compose up -d

echo All services are now running!
echo Aplicación web disponible en http://localhost:8080
pause