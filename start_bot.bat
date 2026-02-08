@echo off
chcp 65001 > nul
title 🤖 Telegram Content Bot
cls

echo ========================================
echo      TELEGRAM CONTENT BOT v3.0
echo ========================================
echo.

REM Активируем окружение
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
    echo ✅ Виртуальное окружение
)

REM Запускаем улучшенного бота
echo.
echo 🚀 Запуск улучшенного бота...
echo.

python improved_bot.py

echo.
echo ========================================
echo.
pause