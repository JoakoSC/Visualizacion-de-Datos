@echo off
title Lanzador de StreamView Analytics
echo Iniciando la aplicacion de Streamlit...
cd /d "%~dp0"
python -m streamlit run visualizacion-de-datos/dashboard/app.py
pause