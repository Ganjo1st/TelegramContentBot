# railway_bot.py - Без изменений
import os
import sys
import time
import logging
import threading
from flask import Flask, jsonify

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/health')
def health():
    return jsonify({"status": "healthy"}), 200

def run_flask():
    port = int(os.getenv("PORT", "8080"))
    logger.info(f"Starting Flask on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

def run_telegram_bot():
    try:
        logger.info("🤖 Starting Telegram bot...")
        import asyncio
        import nest_asyncio
        from no_video_bot import main
        
        nest_asyncio.apply()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        loop.run_until_complete(main())
        
    except Exception as e:
        logger.error(f"❌ Bot error: {e}")

def start_bot():
    while True:
        run_telegram_bot()
        logger.info("🔄 Restarting bot in 30 seconds...")
        time.sleep(30)

if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("🤖 Telegram Bot - Railway")
    logger.info("=" * 50)
    
    bot_thread = threading.Thread(target=start_bot, daemon=True)
    bot_thread.start()
    
    run_flask()
