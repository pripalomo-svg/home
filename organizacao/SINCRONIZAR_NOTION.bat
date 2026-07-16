@echo off
chcp 65001 >nul
echo.
echo  ==========================================
echo   Sincronizar com Notion
echo  ==========================================
echo.

cd /d "%~dp0"

python --version >nul 2>&1
if errorlevel 1 (
    echo  ERRO: Python nao encontrado.
    pause
    exit /b 1
)

if not exist organizacao.db (
    echo  Criando banco...
    python organizacao.py init
    python importar_dados.py pacientes templates\pacientes.csv
    python importar_dados.py atendimentos templates\atendimentos.csv
)

python organizacao.py sincronizar

echo.
echo  Abra index.html para ver os dados atualizados.
echo.
pause
