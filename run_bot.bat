@echo off
chcp 65001 > nul
title 🤖 Telegram Content Bot
cls

echo ========================================
echo      TELEGRAM CONTENT BOT v2.0
echo ========================================
echo.

REM Проверяем виртуальное окружение
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
    echo ✅ Виртуальное окружение активировано
) else (
    echo ⚠ Виртуальное окружение не найдено
    echo 📦 Используем глобальные пакеты
)

REM Проверяем зависимости
echo.
echo 🔍 Проверка зависимостей...
pip install telethon python-telegram-bot httpx aiohttp --quiet 2>nul

REM Запускаем бота
echo.
echo 🚀 Запуск бота...
echo.

python main.py

echo.
echo ========================================
echo.
pause