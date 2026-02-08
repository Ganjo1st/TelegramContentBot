#!/bin/bash

# restart_server.sh - Перезапуск бота

echo "🔄 Перезапуск бота..."

# Останавливаем старый процесс
if [ -f "bot.pid" ]; then
    PID=$(cat bot.pid)
    if kill -0 $PID 2>/dev/null; then
        kill $PID
        echo "✅ Остановлен процесс $PID"
    else
        echo "⚠ Процесс $PID не найден"
    fi
    rm -f bot.pid
fi

# Ждем 5 секунд
sleep 5

# Запускаем заново
./start_server.sh