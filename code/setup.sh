#!/bin/bash

# Function to wait for MariaDB to be ready
wait_for_mariadb() {
  echo "Esperando a la base de datos..."
  until mysqladmin ping -h mariadb --silent; do
    sleep 1
  done
  echo "Base de datos creada!"
}

# Start MariaDB container first
echo "Creando contenedores..."
docker-compose up -d db

# Wait until MariaDB is ready
wait_for_mariadb

# Bring up the rest of the services defined in docker-compose.yaml
echo "Inicializando servicios..."
docker-compose up -d

echo "Todos los servicios están listos!"
echo "Aplicación web disponible en http://localhost:8080"