# no_video_bot.py - Упрощенная версия для Railway
import asyncio
import os
import re
import sys
from datetime import datetime
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument

print("=" * 70)
print("🤖 TELEGRAM CONTENT BOT - Railway Cloud Version")
print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)

# ===== КОНФИГУРАЦИЯ =====
API_ID = int(os.getenv('API_ID', '37267988'))
API_HASH = os.getenv('API_HASH', '0d6a0ea97840273b408297adf779ff80')
SOURCE_CHANNEL = os.getenv('SOURCE_CHANNEL', '@tsargradtv')
TARGET_CHANNEL = os.getenv('TARGET_CHANNEL', '@Chanal_in_1')
SESSION_STRING = os.getenv('TELEGRAM_SESSION_STRING', '')

print(f"🔧 Режим: Railway Cloud")
print(f"📡 Канал-источник: {SOURCE_CHANNEL}")
print(f"📤 Ваш канал: {TARGET_CHANNEL}")
print(f"🔐 API ID: {API_ID}")
print(f"🔐 API Hash: {'***' + API_HASH[-4:] if API_HASH else 'Нет'}")
print("=" * 70)

# ===== ФУНКЦИИ ОБРАБОТКИ =====

async def format_text(text):
    """Форматирование текста для Дзен"""
    if not text:
        return ""
    
    # Удаляем ссылки на Telegram
    text = re.sub(r'https?://t\.me/[^\s]+', '', text)
    text = re.sub(r'@[\w_]+', '', text)
    
    # Заменяем переносы строк
    text = text.replace('\n', '\n\n')
    
    # Удаляем лишние пробелы
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

async def process_photo_message(client, message):
    """Обработка сообщения с фото"""
    try:
        print(f"📸 Найдено фото сообщение от {message.date}")
        
        # Скачиваем фото
        photo_path = await message.download_media(file='downloads/')
        
        if photo_path:
            # Форматируем текст
            caption = await format_text(message.text or message.message)
            
            # Отправляем в целевой канал
            await client.send_file(
                TARGET_CHANNEL,
                photo_path,
                caption=caption[:1024] if caption else None,
                parse_mode='html'
            )
            
            print(f"✅ Фото отправлено в {TARGET_CHANNEL}")
            
            # Удаляем временный файл
            os.remove(photo_path)
        else:
            print("⚠️ Не удалось скачать фото")
            
    except Exception as e:
        print(f"❌ Ошибка обработки фото: {e}")

async def process_text_message(client, message):
    """Обработка текстового сообщения"""
    try:
        print(f"📝 Найдено текстовое сообщение от {message.date}")
        
        # Форматируем текст
        formatted_text = await format_text(message.text or message.message)
        
        if formatted_text:
            # Отправляем в целевой канал
            await client.send_message(
                TARGET_CHANNEL,
                formatted_text,
                parse_mode='html'
            )
            
            print(f"✅ Текст отправлен в {TARGET_CHANNEL}")
        else:
            print("⚠️ Текст пустой после форматирования")
            
    except Exception as e:
        print(f"❌ Ошибка обработки текста: {e}")

async def new_message_handler(event):
    """Обработчик новых сообщений"""
    try:
        message = event.message
        print(f"🆕 Новое сообщение ID: {message.id} | Дата: {message.date}")
        
        # Проверяем тип сообщения
        if message.media:
            if isinstance(message.media, MessageMediaPhoto):
                await process_photo_message(event.client, message)
            elif isinstance(message.media, MessageMediaDocument):
                # Пропускаем видео и документы
                print("⏭️ Пропускаем видео/документ")
            else:
                print(f"ℹ️ Неизвестный тип медиа: {type(message.media)}")
        else:
            await process_text_message(event.client, message)
            
    except Exception as e:
        print(f"🔥 Ошибка в обработчике: {e}")

async def main():
    """Основная функция бота"""
    print("🚀 Запуск основного цикла бота...")
    print(f"⏰ Время старта: {datetime.now().strftime('%H:%M:%S')}")
    
    # Создаем папку для загрузок
    os.makedirs('downloads', exist_ok=True)
    
    # Инициализация клиента
    if SESSION_STRING and SESSION_STRING.strip():
        print("📱 Используется строковая сессия")
        client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
    else:
        print("📱 Создается новая сессия")
        client = TelegramClient('railway_session', API_ID, API_HASH)
    
    try:
        # Запускаем клиент
        await client.start()
        
        # Получаем информацию о себе
        me = await client.get_me()
        print(f"✅ Telethon клиент запущен")
        print(f"👤 ID: {me.id}")
        print(f"📛 Имя: {me.first_name}")
        if me.username:
            print(f"🔗 @{me.username}")
        
        # Регистрируем обработчик
        client.add_event_handler(
            new_message_handler,
            events.NewMessage(chats=SOURCE_CHANNEL)
        )
        
        print(f"👂 Ожидание новых сообщений из {SOURCE_CHANNEL}...")
        print(f"📤 Отправка в: {TARGET_CHANNEL}")
        print("=" * 70)
        print("✅ Бот успешно запущен и работает!")
        print("ℹ️ Логи будут появляться при новых сообщениях")
        print("=" * 70)
        
        # Бесконечный цикл ожидания
        await client.run_until_disconnected()
        
    except Exception as e:
        print(f"❌ Ошибка при запуске: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        print("🔌 Завершение работы...")
        await client.disconnect()

if __name__ == "__main__":
    try:
        # Запуск асинхронной функции
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Бот остановлен пользователем")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
