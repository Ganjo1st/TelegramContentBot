@echo off
chcp 65001 > nul
title 🚀 Final Telegram Bot
cls

echo ========================================
echo      FINAL TELEGRAM CONTENT BOT
echo ========================================
echo.

REM Активируем окружение
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
    echo ✅ Виртуальное окружение активировано
)

REM Устанавливаем зависимости если нужно
echo.
echo 📦 Проверка зависимостей...
pip install telethon python-telegram-bot httpx --quiet >nul 2>&1

echo.
echo 🚀 Запуск бота...
echo.

python final_working_bot.py

echo.
echo ========================================
echo.
pause