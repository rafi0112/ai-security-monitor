@echo off

echo ====================================
echo AI Security Monitor Deployment
echo ====================================

echo Pulling latest code...
git pull

echo Stopping old containers...
docker compose down

echo Rebuilding containers...
docker compose build

echo Starting containers...
docker compose up -d

echo ====================================
echo Deployment Complete
echo ====================================