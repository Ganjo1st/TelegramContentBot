# railway_bot.py
import os
import asyncio
import logging
import threading
import time
from flask import Flask, jsonify
import nest_asyncio
import sys

# Применяем nest_asyncio для совместимости
nest_asyncio.apply()

# Настройка логов
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Создаем Flask-приложение
app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        "status": "online", 
        "service": "TelegramContentBot",
        "version": "1.0"
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy"}), 200

@app.route('/ready')
def ready():
    return jsonify({"status": "ready"}), 200

def run_flask():
    """Запуск Flask сервера"""
    try:
        # Получаем PORT из переменных окружения, преобразуем в int
        port_str = os.getenv("PORT", "8080")
        
        # Проверяем и преобразуем PORT
        if not port_str.isdigit():
            logger.error(f"PORT must be a number, got: {port_str}")
            port = 8080
        else:
            port = int(port_str)
            
            if port < 0 or port > 65535:
                logger.error(f"PORT must be between 0-65535, got: {port}")
                port = 8080
        
        logger.info(f"Starting Flask server on port {port}")
        
        # Важно: use_reloader=False для предотвращения двойного запуска
        app.run(
            host='0.0.0.0', 
            port=port, 
            debug=False, 
            use_reloader=False,
            threaded=True
        )
    except Exception as e:
        logger.error(f"Flask server error: {e}")
        sys.exit(1)

async def run_telegram_bot():
    """Запуск Telegram бота"""
    try:
        # Импортируем ваш основной бот
        logger.info("Importing Telegram bot...")
        from no_video_bot import main
        
        logger.info("Starting Telegram bot logic...")
        await main()
        
    except ImportError as e:
        logger.error(f"Import error: {e}")
        logger.error("Make sure no_video_bot.py is in the same directory")
        return
    except Exception as e:
        logger.error(f"Telegram bot error: {e}")
        raise

def start_telegram_bot():
    """Запуск бота в отдельном потоке"""
    def run_async():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        while True:
            try:
                loop.run_until_complete(run_telegram_bot())
            except Exception as e:
                logger.error(f"Bot crashed: {e}. Restarting in 30 seconds...")
                time.sleep(30)
    
    # Запускаем в отдельном потоке
    bot_thread = threading.Thread(target=run_async, daemon=True)
    bot_thread.start()
    logger.info("Telegram bot thread started")
    return bot_thread

if __name__ == "__main__":
    logger.info("=== TelegramContentBot Startup ===")
    logger.info(f"Python version: {sys.version}")
    
    # Проверяем наличие обязательных переменных
    required_vars = ['API_ID', 'API_HASH']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        logger.error("Please set them in Railway Variables")
    
    # Запускаем Telegram бот в фоне
    bot_thread = start_telegram_bot()
    
    # Запускаем Flask (блокирующий вызов)
    run_flask()
