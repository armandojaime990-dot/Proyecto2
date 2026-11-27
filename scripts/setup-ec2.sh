#!/usr/bin/env bash
# Preparacion UNICA de la instancia EC2 (Ubuntu 24.04). Ejecutar con: bash setup-ec2.sh
set -euo pipefail

echo ">> Instalando Docker y el plugin de Compose"
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker "$USER"

echo ">> Instalando rsync y lm-sensors"
sudo apt-get update -y && sudo apt-get install -y rsync lm-sensors

echo ">> Creando swap de 2 GB (ayuda en instancias pequenas)"
if ! swapon --show | grep -q /swapfile; then
  sudo fallocate -l 2G /swapfile
  sudo chmod 600 /swapfile
  sudo mkswap /swapfile
  sudo swapon /swapfile
  echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
fi

mkdir -p ~/app
echo ">> Listo. Cierra la sesion SSH y vuelve a entrar para usar docker sin sudo."
echo ">> Despues crea ~/app/.env a partir de .env.example"
