@echo off
chcp 65001 >nul
title 智能备课助手

echo ==============================================
echo   智能备课助手 — 大学金融学 AI 备课中心
echo ==============================================
echo.

REM 检查 Python 是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到 Python，请先安装 Python 3.10+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM 检查是否设置了 API Key
if "%DEEPSEEK_API_KEY%"=="" (
    echo [提示] 未设置 DEEPSEEK_API_KEY 环境变量
    echo.
    echo 请先设置环境变量后重新运行：
    echo   set DEEPSEEK_API_KEY=你的DeepSeek_API_Key
    echo   run.bat
    echo.
    echo 或者在当前窗口输入 API Key 后回车：
    set /p DEEPSEEK_API_KEY="请输入 DeepSeek API Key: "
    echo.
)

REM 安装依赖
echo [1/3] 检查依赖...
pip install -r requirements.txt -q 2>nul
if %errorlevel% neq 0 (
    echo [提示] 正在安装依赖包，请稍候...
    pip install fastapi uvicorn openai python-multipart aiofiles
)

REM 启动服务
echo [2/3] 启动 Web 服务...
echo [3/3] 服务已启动！
echo.
echo   👉 本地访问: http://localhost:8000
echo   👉 停止服务: Ctrl + C
echo.
echo ==============================================
echo.

python server.py

pause
