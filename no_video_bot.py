# no_video_bot.py - С видео, длинными постами и подписью ЦарьградТВ
import asyncio
import os
import re
import sys
from datetime import datetime
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument, DocumentAttributeVideo
import mimetypes

print("=" * 70)
print("🤖 TELEGRAM CONTENT BOT - С ВИДЕО И ДЛИННЫМИ ПОСТАМИ")
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
print("=" * 70)

# ===== ФУНКЦИИ ОБРАБОТКИ =====

def split_long_text(text, max_length=4096):
    """Разбивает длинный текст на части для отправки"""
    if len(text) <= max_length:
        return [text]
    
    parts = []
    current_part = ""
    
    # Разбиваем по предложениям
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    for sentence in sentences:
        if len(current_part) + len(sentence) + 1 <= max_length:
            if current_part:
                current_part += " " + sentence
            else:
                current_part = sentence
        else:
            if current_part:
                parts.append(current_part)
            # Если одно предложение слишком длинное, разбиваем его
            if len(sentence) > max_length:
                # Разбиваем длинное предложение на части
                for i in range(0, len(sentence), max_length):
                    parts.append(sentence[i:i+max_length])
            else:
                current_part = sentence
    
    if current_part:
        parts.append(current_part)
    
    return parts

async def format_text(text, add_source=True, is_first_part=True, is_last_part=True):
    """Форматирование текста с учетом разбивки на части"""
    if not text:
        text = ""
    
    # Удаляем ссылки на Telegram
    text = re.sub(r'https?://t\.me/[^\s]+', '', text)
    text = re.sub(r'@[\w_]+', '', text)
    
    # Удаляем эмодзи-флаги и специальные символы
    text = re.sub(r'[\U0001F1E6-\U0001F1FF]{2}', '', text)  # Флаги
    text = re.sub(r'[♺⚠️🔴🟢🟡🔵🟣🟠⚫⚪🟤\u200b\u2060]', '', text)  # Спецсимволы
    
    # Сохраняем переносы строк
    text = text.strip()
    
    # Добавляем подпись только к последней части
    if add_source and is_last_part and text:
        if not text.endswith(('.', '!', '?')):
            text += '.'
        text += f"\n\n📰 Источник: ЦарьградТВ"
    
    return text

async def process_photo_message(client, message):
    """Обработка сообщения с фото"""
    try:
        print(f"📸 Найдено фото сообщение от {message.date}")
        
        # Скачиваем фото
        photo_path = await message.download_media(file='downloads/')
        
        if photo_path:
            # Получаем текст
            original_text = message.text or message.message or ""
            
            # Форматируем текст с подписью
            caption = await format_text(original_text, add_source=True)
            
            # Если текст слишком длинный для caption (1024 символа)
            if len(caption) > 1024:
                print(f"⚠️ Текст слишком длинный ({len(caption)} символов). Разбиваем...")
                
                # Отправляем фото с кратким описанием
                short_caption = caption[:1000] + "...\n\n📰 Источник: ЦарьградТВ"
                await client.send_file(
                    TARGET_CHANNEL,
                    photo_path,
                    caption=short_caption,
                    parse_mode='html'
                )
                
                # Отправляем полный текст отдельными сообщениями
                text_parts = split_long_text(original_text)
                for i, part in enumerate(text_parts):
                    formatted_part = await format_text(
                        part, 
                        add_source=(i == len(text_parts)-1),  # Подпись только к последней части
                        is_last_part=(i == len(text_parts)-1)
                    )
                    if formatted_part.strip():
                        await client.send_message(
                            TARGET_CHANNEL,
                            formatted_part,
                            parse_mode='html'
                        )
                        await asyncio.sleep(0.5)  # Небольшая задержка между сообщениями
                
                print(f"✅ Фото + {len(text_parts)} частей текста отправлено")
            else:
                # Отправляем фото с подписью
                await client.send_file(
                    TARGET_CHANNEL,
                    photo_path,
                    caption=caption if caption else "📰 Источник: ЦарьградТВ",
                    parse_mode='html'
                )
                print(f"✅ Фото с подписью отправлено")
            
            # Удаляем временный файл
            os.remove(photo_path)
        else:
            print("⚠️ Не удалось скачать фото")
            
    except Exception as e:
        print(f"❌ Ошибка обработки фото: {e}")

async def process_video_message(client, message):
    """Обработка видео сообщения"""
    try:
        print(f"🎥 Найдено видео сообщение от {message.date}")
        
        # Получаем информацию о видео
        document = message.media.document
        video_attributes = [attr for attr in document.attributes if isinstance(attr, DocumentAttributeVideo)]
        
        if video_attributes:
            video_info = video_attributes[0]
            print(f"📊 Видео: {video_info.duration}с, {video_info.width}x{video_info.height}")
        
        # Получаем текст
        original_text = message.text or message.message or ""
        
        # Скачиваем видео (в фоне, чтобы не блокировать)
        print(f"⬇️ Скачивание видео... (это может занять время)")
        video_path = await message.download_media(file='downloads/')
        
        if video_path:
            # Форматируем текст с подписью
            caption = await format_text(original_text, add_source=True)
            
            # Для видео ограничение caption тоже 1024 символа
            if len(caption) > 1024:
                print(f"⚠️ Текст слишком длинный ({len(caption)} символов). Разбиваем...")
                
                # Отправляем видео с кратким описанием
                short_caption = caption[:1000] + "...\n\n📰 Источник: ЦарьградТВ"
                await client.send_file(
                    TARGET_CHANNEL,
                    video_path,
                    caption=short_caption,
                    parse_mode='html'
                )
                
                # Отправляем полный текст отдельными сообщениями
                text_parts = split_long_text(original_text)
                for i, part in enumerate(text_parts):
                    formatted_part = await format_text(
                        part,
                        add_source=(i == len(text_parts)-1),
                        is_last_part=(i == len(text_parts)-1)
                    )
                    if formatted_part.strip():
                        await client.send_message(
                            TARGET_CHANNEL,
                            formatted_part,
                            parse_mode='html'
                        )
                        await asyncio.sleep(0.5)
                
                print(f"✅ Видео + {len(text_parts)} частей текста отправлено")
            else:
                # Отправляем видео с подписью
                await client.send_file(
                    TARGET_CHANNEL,
                    video_path,
                    caption=caption if caption else "📰 Источник: ЦарьградТВ",
                    parse_mode='html',
                    supports_streaming=True  # Важно для видео!
                )
                print(f"✅ Видео с подписью отправлено")
            
            # Удаляем временный файл
            os.remove(video_path)
        else:
            print("⚠️ Не удалось скачать видео")
            
    except Exception as e:
        print(f"❌ Ошибка обработки видео: {e}")

async def process_text_message(client, message):
    """Обработка текстового сообщения"""
    try:
        print(f"📝 Найдено текстовое сообщение от {message.date}")
        
        # Получаем текст
        original_text = message.text or message.message or ""
        
        # Разбиваем длинный текст на части
        text_parts = split_long_text(original_text)
        
        if len(text_parts) > 1:
            print(f"⚠️ Длинный текст ({len(original_text)} символов). Разбиваем на {len(text_parts)} частей")
        
        # Отправляем каждую часть
        for i, part in enumerate(text_parts):
            # Форматируем текст (подпись только к последней части)
            formatted_text = await format_text(
                part,
                add_source=(i == len(text_parts)-1),
                is_last_part=(i == len(text_parts)-1)
            )
            
            if formatted_text.strip():
                await client.send_message(
                    TARGET_CHANNEL,
                    formatted_text,
                    parse_mode='html'
                )
                print(f"✅ Часть {i+1}/{len(text_parts)} отправлена")
                await asyncio.sleep(0.5)  # Задержка между частями
        
        print(f"✅ Всего отправлено: {len(text_parts)} частей")
        print(f"📝 Подпись добавлена: ЦарьградТВ")
            
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
                # Проверяем, является ли документ видео
                document = message.media.document
                is_video = False
                
                # Проверяем атрибуты документа
                for attr in document.attributes:
                    if isinstance(attr, DocumentAttributeVideo):
                        is_video = True
                        break
                
                # Также проверяем MIME тип
                mime_type = getattr(document, 'mime_type', '')
                if mime_type and mime_type.startswith('video/'):
                    is_video = True
                
                if is_video:
                    await process_video_message(event.client, message)
                else:
                    print(f"⏭️ Пропускаем документ (не видео): {mime_type}")
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
        print("📝 Длинные посты будут разбиты на части")
        print("🎥 Видео будут копироваться")
        print("📰 Подпись: ЦарьградТВ добавляется в конец")
        print("=" * 70)
        print("✅ Бот успешно запущен и работает!")
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
