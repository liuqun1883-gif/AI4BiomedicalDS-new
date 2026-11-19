@echo off
cd /d "%~dp0"
set "MPLCONFIGDIR=%~dp0.venv\matplotlib-cache"
set "JUPYTER_CONFIG_DIR=%~dp0.venv\jupyter-config"
set "JUPYTER_RUNTIME_DIR=%~dp0.venv\jupyter-runtime"
"%~dp0.venv\Scripts\python.exe" -m notebook "3. High-dimension\notebook\high-dimension-lab.ipynb"
