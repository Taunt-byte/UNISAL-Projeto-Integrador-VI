@echo off
REM Inicia o NetMonitor (Projeto Integrador VI)
REM Use "iniciar.bat --rede" para liberar o acesso de outros dispositivos da rede
cd /d "%~dp0"
if not exist .venv (
    echo Criando ambiente virtual...
    python -m venv .venv
)
call .venv\Scripts\activate.bat
echo Verificando dependencias...
pip install -q -r requirements.txt
echo.
echo Abra no navegador: http://127.0.0.1:5000   (Ctrl+C para parar)
python app.py %*
pause
