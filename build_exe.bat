@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ============================================================
echo   BUILD - Inclusao CADIN
echo ============================================================
echo.

set PYTHON=python

%PYTHON% --version >nul 2>&1
if errorlevel 1 (
    set PYTHON=py
)

%PYTHON% --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado. Instale o Python para gerar o .exe.
    pause
    exit /b 1
)

echo [1/5] Atualizando pip...
%PYTHON% -m pip install --upgrade pip
if errorlevel 1 (
    echo [ERRO] Falha ao atualizar pip.
    pause
    exit /b 1
)

echo.
echo [2/5] Instalando dependencias do projeto...
%PYTHON% -m pip install -r "%~dp0requirements.txt"
if errorlevel 1 (
    echo [ERRO] Falha ao instalar dependencias.
    pause
    exit /b 1
)

echo.
echo [3/5] Instalando/atualizando PyInstaller...
%PYTHON% -m pip install --upgrade pyinstaller
if errorlevel 1 (
    echo [ERRO] Falha ao instalar PyInstaller.
    pause
    exit /b 1
)

echo.
echo [4/5] Gerando icones (PNG/ICO)...
%PYTHON% "%~dp0assets\gerar_icones.py"
if errorlevel 1 (
    echo [ERRO] Falha ao gerar icones.
    pause
    exit /b 1
)

echo.
echo [5/5] Gerando executavel. Isso pode demorar alguns minutos...
echo       Fechando InclusaoCADIN.exe se estiver aberto...
taskkill /IM InclusaoCADIN.exe /F >nul 2>&1
timeout /t 2 /nobreak >nul

if exist "%~dp0build" (
    rmdir /s /q "%~dp0build" 2>nul
    if exist "%~dp0build" (
        echo [AVISO] Nao foi possivel apagar a pasta build. Feche o app e tente de novo.
        pause
        exit /b 1
    )
)
if exist "%~dp0dist" (
    rmdir /s /q "%~dp0dist" 2>nul
    if exist "%~dp0dist" (
        echo [AVISO] Nao foi possivel apagar a pasta dist. Feche o app e tente de novo.
        pause
        exit /b 1
    )
)

REM Sem --clean: evita PermissionError no OneDrive quando a pasta build esta bloqueada
%PYTHON% -m PyInstaller "%~dp0InclusaoCADIN.spec" --noconfirm
if errorlevel 1 (
    echo.
    echo [ERRO] Falha ao gerar o executavel. Veja o log acima.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   CONCLUIDO!
echo   Executavel gerado em:
echo   %~dp0dist\InclusaoCADIN.exe
echo.
echo   Para enviar ao colega, mande o arquivo acima.
echo   Ele precisa ter Google Chrome instalado.
echo ============================================================
echo.
pause
