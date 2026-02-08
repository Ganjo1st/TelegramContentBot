@echo off
chcp 65001 > nul
title 🚫 No Video Bot
cls

echo ========================================
echo      TELEGRAM BOT - NO VIDEO COPY
echo ========================================
echo.

if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
    echo ✅ Виртуальное окружение
)

echo.
echo 🚀 Запуск бота (пропускает посты с видео)...
echo.

python no_video_bot.py

echo.
echo ========================================
echo.
pause