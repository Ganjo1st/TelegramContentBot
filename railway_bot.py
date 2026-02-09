# railway_bot.py
import os
import sys
import time
import logging
import threading
from flask import Flask, jsonify

# Настройка логов
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
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
    """Запуск Flask сервера"""
    try:
        port = int(os.getenv("PORT", "8080"))
        if not 0 <= port <= 65535:
            port = 8080
        logger.info(f"Starting Flask server on port {port}")
        app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
    except Exception as e:
        logger.error(f"Flask error: {e}")
        sys.exit(1)

def run_telegram_bot():
    """Запуск Telegram бота в отдельном потоке"""
    try:
        # Импортируем здесь, чтобы ошибки импорта были видны в логах
        import asyncio
        import nest_asyncio
        nest_asyncio.apply()
        
        # Импортируем ваш бот
        logger.info("Importing no_video_bot...")
        from no_video_bot import main
        
        logger.info("Starting Telegram bot...")
        
        # Запускаем бота в цикле событий
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        while True:
            try:
                loop.run_until_complete(main())
            except Exception as e:
                logger.error(f"Bot error: {e}. Restarting in 30 seconds...")
                time.sleep(30)
                
    except ImportError as e:
        logger.error(f"Cannot import modules: {e}")
        logger.error("Please check requirements.txt")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")

if __name__ == "__main__":
    logger.info("=== Starting TelegramContentBot ===")
    
    # Проверяем переменные окружения
    required = ['API_ID', 'API_HASH', 'SESSION_NAME', 'SOURCE_CHANNEL', 'TARGET_CHANNEL']
    missing = [var for var in required if not os.getenv(var)]
    
    if missing:
        logger.warning(f"Missing env variables: {missing}")
        logger.warning("Bot may not work properly")
    
    # Запускаем Telegram бот в отдельном потоке
    bot_thread = threading.Thread(target=run_telegram_bot, daemon=True)
    bot_thread.start()
    
    # Запускаем Flask (блокирует основной поток)
    run_flask()
