@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

set LOG=build_log.txt
echo ============================================================ > "%LOG%"
echo   Central de Mapas - gerando o executavel >> "%LOG%"
echo   Data/hora: %date% %time% >> "%LOG%"
echo ============================================================ >> "%LOG%"

echo ============================================================
echo   Central de Mapas - gerando o executavel (.exe)
echo   (tudo que aparecer aqui tambem fica salvo em build_log.txt)
echo ============================================================
echo.

echo [1/5] Verificando se o Python esta instalado...
echo [1/5] Verificando Python... >> "%LOG%"
where python >> "%LOG%" 2>&1
if errorlevel 1 (
    echo.
    echo [ERRO] O comando "python" nao foi encontrado neste computador.
    echo Instale o Python em https://www.python.org/downloads/ marcando
    echo a opcao "Add python.exe to PATH" durante a instalacao.
    echo [ERRO] python nao encontrado - comando "where python" falhou >> "%LOG%"
    echo.
    echo Detalhes salvos em build_log.txt
    pause
    exit /b 1
)

python --version >> "%LOG%" 2>&1
python --version
if errorlevel 1 (
    echo.
    echo [ERRO] O Python foi encontrado mas nao executa corretamente.
    echo Isso costuma acontecer quando o "python" instalado e um atalho
    echo da Microsoft Store que nao funciona. Reinstale o Python pelo
    echo site oficial: https://www.python.org/downloads/
    echo [ERRO] python --version falhou >> "%LOG%"
    echo.
    echo Detalhes salvos em build_log.txt
    pause
    exit /b 1
)

echo.
echo [2/5] Instalando/atualizando as bibliotecas necessarias...
echo (isso pode demorar alguns minutos na primeira vez)
echo [2/5] Instalando bibliotecas... >> "%LOG%"
python -m pip install --upgrade customtkinter pypdf img2pdf pyinstaller >> "%LOG%" 2>&1
if errorlevel 1 (
    echo.
    echo [ERRO] Nao foi possivel instalar as bibliotecas.
    echo Verifique sua conexao com a internet.
    echo Veja os detalhes completos em build_log.txt
    echo.
    pause
    exit /b 1
)
echo Bibliotecas instaladas com sucesso.

echo.
echo [3/5] Limpando builds antigas (garante que o icone novo seja aplicado)...
echo [3/5] Limpando build/dist... >> "%LOG%"
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

echo.
echo [4/5] Gerando o executavel a partir de CentralDeMapas.spec...
echo (esta etapa e a mais demorada, pode levar alguns minutos, aguarde)
echo [4/5] Rodando PyInstaller... >> "%LOG%"
python -m PyInstaller --noconfirm --clean CentralDeMapas.spec >> "%LOG%" 2>&1
set PYI_RESULT=%errorlevel%
echo Codigo de saida do PyInstaller: %PYI_RESULT% >> "%LOG%"

echo.
echo [5/5] Verificando resultado...
if exist "dist\CentralDeMapas.exe" (
    echo Copiando o novo executavel para a pasta principal...
    del /f /q "Central de Mapas.exe" >nul 2>&1
    copy /Y "dist\CentralDeMapas.exe" "Central de Mapas.exe" >nul
    echo ============================================================ >> "%LOG%"
    echo SUCESSO: exe copiado >> "%LOG%"
    echo.
    echo ============================================================
    echo   PRONTO! "Central de Mapas.exe" foi atualizado com sucesso.
    echo.
    echo   Se o icone ainda aparecer errado no Explorador de Arquivos
    echo   ou na barra de tarefas, isso costuma ser cache de icone do
    echo   Windows ^(nao um problema no arquivo^). Para forcar a
    echo   atualizacao, feche o Explorador e rode os comandos abaixo
    echo   em um terminal:
    echo.
    echo       taskkill /f /im explorer.exe
    echo       start explorer.exe
    echo ============================================================
) else (
    echo ============================================================ >> "%LOG%"
    echo FALHA: dist\CentralDeMapas.exe nao foi criado >> "%LOG%"
    echo ============================================================
    echo   [ERRO] O executavel NAO foi gerado.
    echo.
    echo   Abra o arquivo build_log.txt que esta nesta mesma pasta e
    echo   envie o conteudo dele para eu poder identificar o problema
    echo   exato. As ultimas linhas do PyInstaller sao as mais
    echo   importantes.
    echo ============================================================
)

echo.
echo Um arquivo "build_log.txt" foi salvo nesta pasta com todos os
echo detalhes desta execucao.
echo.
pause
