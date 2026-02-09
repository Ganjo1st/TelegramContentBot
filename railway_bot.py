# railway_bot.py
import os
import sys
import time
import logging
import threading
import traceback
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
    return jsonify({
        "status": "online", 
        "service": "TelegramContentBot",
        "timestamp": time.time()
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "bot": "running"}), 200

@app.route('/status')
def status():
    return jsonify({
        "status": "operational",
        "bot_thread": bot_thread.is_alive() if 'bot_thread' in globals() else False
    })

def run_flask():
    """Запуск Flask сервера"""
    try:
        port = int(os.getenv("PORT", "8080"))
        if not 0 <= port <= 65535:
            port = 8080
        
        # Для production используем waitress вместо dev сервера
        if os.getenv("RAILWAY_ENVIRONMENT") == "production":
            from waitress import serve
            logger.info(f"Starting production server (waitress) on port {port}")
            serve(app, host='0.0.0.0', port=port, threads=4)
        else:
            logger.info(f"Starting development server on port {port}")
            app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
            
    except Exception as e:
        logger.error(f"Flask server error: {e}")
        traceback.print_exc()
        sys.exit(1)

def run_telegram_bot():
    """Запуск Telegram бота в отдельном потоке"""
    max_retries = 10
    retry_delay = 30
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Attempt {attempt + 1}/{max_retries} to start Telegram bot")
            
            # Импортируем необходимые библиотеки
            import asyncio
            import nest_asyncio
            nest_asyncio.apply()
            
            # Проверяем наличие всех зависимостей
            logger.info("Checking dependencies...")
            import aiofiles
            import aiohttp
            import telethon
            logger.info("All dependencies loaded successfully")
            
            # Импортируем ваш бот
            logger.info("Importing no_video_bot...")
            from no_video_bot import main
            
            logger.info("Starting Telegram bot main function...")
            
            # Создаем и настраиваем event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Запускаем бота
            loop.run_until_complete(main())
            
            # Если бот завершился (не должен), перезапускаем
            logger.warning("Bot finished unexpectedly. Restarting...")
            time.sleep(retry_delay)
            
        except ImportError as e:
            logger.error(f"Missing dependency: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            # Выводим список установленных пакетов для отладки
            try:
                import pkg_resources
                installed = [pkg.key for pkg in pkg_resources.working_set]
                logger.info(f"Installed packages: {', '.join(sorted(installed))}")
            except:
                pass
                
            logger.error(f"Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)
            
        except Exception as e:
            logger.error(f"Bot error on attempt {attempt + 1}: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                logger.error("Max retries reached. Bot stopped.")
                break

# Глобальная переменная для отслеживания потока
bot_thread = None

if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("TelegramContentBot - Railway Deployment")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Working directory: {os.getcwd()}")
    logger.info("=" * 50)
    
    # Проверяем наличие файлов
    files_to_check = ['no_video_bot.py', 'requirements.txt']
    for file in files_to_check:
        if os.path.exists(file):
            logger.info(f"✓ Found: {file}")
        else:
            logger.warning(f"✗ Missing: {file}")
    
    # Проверяем переменные окружения
    required_vars = ['API_ID', 'API_HASH', 'SESSION_NAME']
    env_vars = {}
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Скрываем чувствительные данные
            if var in ['API_HASH'] and len(value) > 8:
                env_vars[var] = value[:4] + "..." + value[-4:]
            elif var == 'API_ID':
                env_vars[var] = value
            elif var == 'SESSION_NAME':
                env_vars[var] = value
        else:
            env_vars[var] = "NOT SET"
            logger.warning(f"⚠ Environment variable {var} is not set!")
    
    logger.info(f"Environment: {env_vars}")
    
    # Запускаем Telegram бот в отдельном потоке
    logger.info("Starting Telegram bot thread...")
    bot_thread = threading.Thread(target=run_telegram_bot, daemon=True, name="TelegramBot")
    bot_thread.start()
    
    # Даем боту время на инициализацию
    time.sleep(5)
    
    # Проверяем, жив ли поток бота
    if bot_thread.is_alive():
        logger.info("✓ Telegram bot thread is running")
    else:
        logger.warning("⚠ Telegram bot thread may have failed to start")
    
    # Запускаем Flask сервер (блокирующий вызов)
    logger.info("Starting Flask healthcheck server...")
    run_flask()
