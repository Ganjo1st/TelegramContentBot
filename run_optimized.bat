@echo off
chcp 65001 > nul
title 🚀 Оптимизированный Telegram Бот
cls

echo ========================================
echo      ОПТИМИЗИРОВАННЫЙ TELEGRAM БОТ
echo ========================================
echo.

if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
    echo ✅ Виртуальное окружение
)

echo.
echo 🚀 Запуск оптимизированного бота...
echo.

python optimized_bot.py

echo.
echo ========================================
echo.
pause