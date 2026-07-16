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

echo  [2/5] Importando pacientes, financas, agenda...
python preencher_pacientes_horarios.py
python importar_dados.py pacientes templates\pacientes.csv
python -c "import sqlite3;c=sqlite3.connect('organizacao.db');c.execute(\"UPDATE pacientes SET status='alta' WHERE nome LIKE 'Paciente %%preencher%%' OR codigo IN ('PAC-019','PAC-020')\");c.commit()"
python importar_dados.py atendimentos templates\atendimentos.csv
python importar_dados.py agenda templates\agenda.csv
python importar_prontuarios.py csv templates\prontuarios.csv

echo  [3/5] Gerando painel de investimentos...
python gerar_investimentos.py

echo  [4/5] Gerando painel principal...
python gerar_dashboard.py

echo  [5/5] Concluido!

echo.
echo  PRONTO! Abra estes arquivos no navegador:
echo    - index.html
echo    - investimentos.html
echo.
pause
