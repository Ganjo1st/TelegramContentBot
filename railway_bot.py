# railway_bot.py - Упрощенный healthcheck сервер
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

# Создаем Flask-приложение
app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        "status": "online", 
        "service": "TelegramContentBot",
        "time": time.time()
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy"}), 200

@app.route('/status')
def status():
    return jsonify({
        "status": "running",
        "bot": "active"
    })

def run_flask():
    """Запуск Flask сервера"""
    try:
        port = int(os.getenv("PORT", "8080"))
        logger.info(f"🚀 Starting Flask server on port {port}")
        app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
    except Exception as e:
        logger.error(f"❌ Flask error: {e}")
        sys.exit(1)

def run_telegram_bot():
    """Запуск Telegram бота"""
    try:
        logger.info("🤖 Importing Telegram bot...")
        
        # Импортируем основной бот
        from no_video_bot import main
        
        logger.info("🚀 Starting Telegram bot main function...")
        
        # Импортируем asyncio и запускаем
        import asyncio
        import nest_asyncio
        nest_asyncio.apply()
        
        # Создаем event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Запускаем бота
        loop.run_until_complete(main())
        
    except ImportError as e:
        logger.error(f"📦 Missing dependency: {e}")
    except Exception as e:
        logger.error(f"❌ Bot error: {e}")
        import traceback
        traceback.print_exc()

def start_bot():
    """Запуск бота с перезапуском при ошибках"""
    while True:
        try:
            run_telegram_bot()
        except Exception as e:
            logger.error(f"🔥 Bot crashed: {e}. Restarting in 30 seconds...")
            time.sleep(30)

if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("🤖 TelegramContentBot - Railway Deployment")
    logger.info("=" * 50)
    
    # Проверяем переменные окружения
    required = ['API_ID', 'API_HASH', 'SOURCE_CHANNEL', 'TARGET_CHANNEL']
    for var in required:
        if not os.getenv(var):
            logger.warning(f"⚠️  Variable {var} is not set")
    
    # Запускаем бота в отдельном потоке
    logger.info("🚀 Starting Telegram bot thread...")
    bot_thread = threading.Thread(target=start_bot, daemon=True)
    bot_thread.start()
    
    # Даем боту время на запуск
    time.sleep(5)
    
    # Проверяем запуск
    if bot_thread.is_alive():
        logger.info("✅ Telegram bot is running")
    else:
        logger.error("❌ Telegram bot failed to start")
    
    # Запускаем Flask (блокирует основной поток)
    logger.info("🌐 Starting healthcheck server...")
    run_flask()
