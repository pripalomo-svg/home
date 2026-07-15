@echo off
chcp 65001 >nul
echo.
echo  ========================================
echo   Atualizando paineis da Organizacao...
echo  ========================================
echo.

cd /d "%~dp0"

python --version >nul 2>&1
if errorlevel 1 (
    echo  ERRO: Python nao encontrado.
    echo  Instale em https://python.org e marque "Add to PATH"
    pause
    exit /b 1
)

if not exist organizacao.db (
    echo  Criando banco pela primeira vez...
    python organizacao.py init
)

echo  [1/4] Importando investimentos...
python importar_investimentos.py templates\investimentos.csv

echo  [2/4] Importando pacientes, financas, agenda...
python importar_dados.py todos

echo  [3/4] Gerando painel de investimentos...
python gerar_investimentos.py

echo  [4/4] Gerando painel principal...
python gerar_dashboard.py

echo.
echo  PRONTO! Abra estes arquivos no navegador:
echo    - index.html
echo    - investimentos.html
echo.
pause
