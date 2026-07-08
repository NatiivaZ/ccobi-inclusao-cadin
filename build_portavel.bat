@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ============================================================
echo   BUILD PORTAVEL - Inclusao CADIN
echo ============================================================
echo.

set PYTHON=python

%PYTHON% --version >nul 2>&1
if errorlevel 1 (
    set PYTHON=py
)

%PYTHON% --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado. Instale o Python para gerar o pacote.
    pause
    exit /b 1
)

echo [1/5] Instalando dependencias...
%PYTHON% -m pip install -r "%~dp0requirements.txt"
if errorlevel 1 (
    echo [ERRO] Falha ao instalar dependencias.
    pause
    exit /b 1
)

echo.
echo [2/5] Instalando/atualizando PyInstaller...
%PYTHON% -m pip install --upgrade pyinstaller
if errorlevel 1 (
    echo [ERRO] Falha ao instalar PyInstaller.
    pause
    exit /b 1
)

echo.
echo [3/5] Gerando icones...
%PYTHON% "%~dp0assets\gerar_icones.py"
if errorlevel 1 (
    echo [ERRO] Falha ao gerar icones.
    pause
    exit /b 1
)

echo.
echo [4/5] Gerando pasta portavel...
taskkill /IM InclusaoCADIN.exe /F >nul 2>&1
timeout /t 2 /nobreak >nul

if exist "%~dp0build" rmdir /s /q "%~dp0build" 2>nul
if exist "%~dp0dist\InclusaoCADIN_Portavel" rmdir /s /q "%~dp0dist\InclusaoCADIN_Portavel" 2>nul
if exist "%~dp0dist\InclusaoCADIN_Portavel.zip" del /q "%~dp0dist\InclusaoCADIN_Portavel.zip" 2>nul

%PYTHON% -m PyInstaller "%~dp0InclusaoCADIN_portavel.spec" --noconfirm
if errorlevel 1 (
    echo [ERRO] Falha ao gerar a pasta portavel.
    pause
    exit /b 1
)

echo.
echo [5/5] Compactando pacote...
timeout /t 5 /nobreak >nul
powershell -NoProfile -ExecutionPolicy Bypass -Command "Compress-Archive -Path '%~dp0dist\InclusaoCADIN_Portavel' -DestinationPath '%~dp0dist\InclusaoCADIN_Portavel.zip' -Force"
if errorlevel 1 (
    echo [AVISO] Primeira tentativa falhou. Aguardando e tentando novamente...
    timeout /t 10 /nobreak >nul
    powershell -NoProfile -ExecutionPolicy Bypass -Command "Compress-Archive -Path '%~dp0dist\InclusaoCADIN_Portavel' -DestinationPath '%~dp0dist\InclusaoCADIN_Portavel.zip' -Force"
    if errorlevel 1 (
        echo [ERRO] Falha ao compactar o pacote.
        echo        Envie a pasta dist\InclusaoCADIN_Portavel manualmente, se ela tiver sido gerada.
        pause
        exit /b 1
    )
)

echo.
echo ============================================================
echo   CONCLUIDO!
echo   Envie este arquivo:
echo   %~dp0dist\InclusaoCADIN_Portavel.zip
echo.
echo   No outro computador: extrair a pasta e executar:
echo   InclusaoCADIN_Portavel\InclusaoCADIN.exe
echo ============================================================
echo.
pause
