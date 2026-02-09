# railway_bot.py
import os
import asyncio
import logging
from threading import Thread
from flask import Flask, jsonify
import nest_asyncio

# Применяем nest_asyncio для совместимости с Flask
nest_asyncio.apply()

# Настройка логов
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Создаем Flask-приложение для healthcheck
app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({"status": "online", "service": "TelegramContentBot"})

@app.route('/health')
def health():
    return jsonify({"status": "healthy"}), 200

def run_flask():
    """Запуск Flask сервера в отдельном потоке"""
    port = int(os.getenv("PORT", 8080))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

async def main_bot_logic():
    """Основная логика бота (ваш существующий код)"""
    try:
        # Импортируем ваш основной бот
        from no_video_bot import main
        
        logger.info("Запуск основного бота...")
        await main()
        
    except Exception as e:
        logger.error(f"Ошибка в основном боте: {e}")
        raise

async def run_bot():
    """Запуск бота с обработкой ошибок"""
    while True:
        try:
            await main_bot_logic()
        except Exception as e:
            logger.error(f"Бот упал с ошибкой: {e}. Перезапуск через 10 секунд...")
            await asyncio.sleep(10)

def start_bot():
    """Запуск бота в asyncio loop"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_bot())

if __name__ == "__main__":
    logger.info("Запуск TelegramContentBot на Railway...")
    
    # Запускаем Flask в отдельном потоке
    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Запускаем бота
    start_bot()
