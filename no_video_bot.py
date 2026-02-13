# no_video_bot.py - ИСПРАВЛЕННАЯ ВЕРСИЯ
import asyncio
import os
import re
import sys
from datetime import datetime
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument, DocumentAttributeVideo, DocumentAttributeFilename

print("=" * 70)
print("🤖 TELEGRAM CONTENT BOT - КОПИРУЕТ ВСЕ ПОСТЫ")
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
print("=" * 70)

def remove_link_paragraphs(text):
    """Удаляет целые абзацы, содержащие ссылки"""
    if not text:
        return text
    
    # Разбиваем на абзацы (по двойному переносу строки)
    paragraphs = text.split('\n\n')
    
    # Фильтруем абзацы, удаляя те, что содержат ссылки
    filtered_paragraphs = []
    
    for para in paragraphs:
        # Проверяем, содержит ли абзац ссылки
        has_link = False
        
        # Разные паттерны ссылок
        link_patterns = [
            r'https?://\S+',           # http:// или https://
            r't\.me/\S+',               # t.me/...
            r'telegram\.me/\S+',        # telegram.me/...
            r'@\w+',                     # @username
            r'подписывайся',             # слово "подписывайся"
            r'подписаться',               # слово "подписаться"
            r'присоединяйся',             # слово "присоединяйся"
            r'переходи по ссылке',        # фраза "переходи по ссылке"
        ]
        
        for pattern in link_patterns:
            if re.search(pattern, para, re.IGNORECASE):
                has_link = True
                print(f"🔗 Удален абзац со ссылкой")
                break
        
        # Если абзац не содержит ссылок, оставляем его
        if not has_link and para.strip():
            filtered_paragraphs.append(para)
    
    # Собираем обратно
    return '\n\n'.join(filtered_paragraphs)

async def clean_text(text):
    """Очистка текста от ссылок и мусора"""
    if not text:
        return ""
    
    # Удаляем абзацы со ссылками
    text = remove_link_paragraphs(text)
    
    # Дополнительная очистка одиночных ссылок
    text = re.sub(r'https?://\S+', '', text)
    text = re.sub(r't\.me/\S+', '', text)
    text = re.sub(r'@\w+', '', text)
    
    # Удаляем пустые строки и лишние пробелы
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    text = '\n'.join(lines)
    
    # Удаляем эмодзи-флаги и специальные символы
    text = re.sub(r'[\U0001F1E6-\U0001F1FF]{2}', '', text)
    text = re.sub(r'[♺⚠️🔴🟢🟡🔵🟣🟠⚫⚪🟤\u200b\u2060]', '', text)
    
    return text.strip()

async def format_with_signature(text):
    """Добавляет подпись в конец текста"""
    if not text:
        return "📰 Источник: ЦарьградТВ"
    
    # Добавляем подпись
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
            # Получаем и очищаем текст
            original_text = message.text or message.message or ""
            cleaned_text = await clean_text(original_text)
            
            if cleaned_text:
                print(f"📝 Текст после очистки: {len(cleaned_text)} символов")
                
                # Форматируем с подписью
                final_text = await format_with_signature(cleaned_text)
                
                # Проверяем длину для caption (макс 1024 символа)
                if len(final_text) <= 1024:
                    # Отправляем фото с подписью
                    await client.send_file(
                        TARGET_CHANNEL,
                        photo_path,
                        caption=final_text,
                        parse_mode='html'
                    )
                    print(f"✅ Фото с подписью отправлено")
                else:
                    # Отправляем фото отдельно
                    await client.send_file(
                        TARGET_CHANNEL,
                        photo_path
                    )
                    print(f"✅ Фото отправлено отдельно")
                    
                    # Отправляем текст отдельно
                    await client.send_message(
                        TARGET_CHANNEL,
                        final_text,
                        parse_mode='html',
                        link_preview=False
                    )
                    print(f"✅ Текст отправлен отдельно ({len(final_text)} символов)")
            else:
                # Если текст пустой после очистки, отправляем только фото
                await client.send_file(
                    TARGET_CHANNEL,
                    photo_path,
                    caption="📰 Источник: ЦарьградТВ"
                )
                print(f"✅ Фото с подписью отправлено (текст удален)")
            
            # Удаляем временный файл
            os.remove(photo_path)
        else:
            print("⚠️ Не удалось скачать фото")
            
    except Exception as e:
        print(f"❌ Ошибка обработки фото: {e}")

async def process_video_message(client, message):
    """Обработка видео сообщения - ИСПРАВЛЕНО"""
    try:
        print(f"🎥 Найдено видео сообщение от {message.date}")
        
        # Получаем информацию о видео безопасно
        document = message.media.document
        
        # Пытаемся получить информацию о видео
        duration = None
        video_info = "видео"
        
        for attr in document.attributes:
            if isinstance(attr, DocumentAttributeVideo):
                # В разных версиях Telethon разные названия атрибутов
                duration = getattr(attr, 'duration', None)
                if hasattr(attr, 'w') and hasattr(attr, 'h'):
                    video_info = f"{duration}с, {attr.w}x{attr.h}" if duration else f"{attr.w}x{attr.h}"
                elif hasattr(attr, 'width') and hasattr(attr, 'height'):
                    video_info = f"{duration}с, {attr.width}x{attr.height}" if duration else f"{attr.width}x{attr.height}"
                break
        
        print(f"📊 {video_info}")
        
        # Получаем и очищаем текст
        original_text = message.text or message.message or ""
        cleaned_text = await clean_text(original_text)
        
        # Скачиваем видео
        print(f"⬇️ Скачивание видео... (это может занять время)")
        video_path = await message.download_media(file='downloads/')
        
        if video_path:
            # Подготавливаем текст
            final_text = await format_with_signature(cleaned_text) if cleaned_text else "📰 Источник: ЦарьградТВ"
            
            # Отправляем видео
            if len(final_text) <= 1024:
                # Если текст короткий - отправляем с видео
                await client.send_file(
                    TARGET_CHANNEL,
                    video_path,
                    caption=final_text,
                    supports_streaming=True,
                    parse_mode='html'
                )
                print(f"✅ Видео с подписью отправлено")
            else:
                # Если текст длинный - отправляем видео отдельно
                await client.send_file(
                    TARGET_CHANNEL,
                    video_path,
                    supports_streaming=True
                )
                print(f"✅ Видео отправлено")
                
                # И текст отдельно
                await client.send_message(
                    TARGET_CHANNEL,
                    final_text,
                    parse_mode='html',
                    link_preview=False
                )
                print(f"✅ Текст отправлен отдельно ({len(final_text)} символов)")
            
            # Удаляем временный файл
            os.remove(video_path)
        else:
            print("⚠️ Не удалось скачать видео")
            
    except Exception as e:
        print(f"❌ Ошибка обработки видео: {e}")
        import traceback
        traceback.print_exc()

async def process_text_message(client, message):
    """Обработка текстового сообщения"""
    try:
        print(f"📝 Найдено текстовое сообщение от {message.date}")
        
        # Получаем и очищаем текст
        original_text = message.text or message.message or ""
        cleaned_text = await clean_text(original_text)
        
        if cleaned_text:
            # Форматируем с подписью
            final_text = await format_with_signature(cleaned_text)
            
            # Отправляем (Telegram поддерживает до 4096 символов)
            await client.send_message(
                TARGET_CHANNEL,
                final_text,
                parse_mode='html',
                link_preview=False
            )
            
            print(f"✅ Текст отправлен ({len(final_text)} символов)")
        else:
            print(f"⚠️ Текст пустой после очистки - пропускаем")
            
    except Exception as e:
        print(f"❌ Ошибка обработки текста: {e}")

async def new_message_handler(event):
    """Обработчик ВСЕХ новых сообщений"""
    try:
        message = event.message
        print(f"🆕 Новое сообщение ID: {message.id} | Дата: {message.date}")
        
        # Обрабатываем ВСЕ типы сообщений
        if message.media:
            if isinstance(message.media, MessageMediaPhoto):
                await process_photo_message(event.client, message)
            elif isinstance(message.media, MessageMediaDocument):
                # Проверяем, является ли документ видео
                document = message.media.document
                is_video = False
                
                # Проверяем атрибуты
                for attr in document.attributes:
                    if isinstance(attr, DocumentAttributeVideo):
                        is_video = True
                        break
                
                # Проверяем MIME тип
                mime_type = getattr(document, 'mime_type', '')
                if mime_type and ('video/' in mime_type or 'mp4' in mime_type):
                    is_video = True
                
                if is_video:
                    await process_video_message(event.client, message)
                else:
                    # Если есть текст, обрабатываем как текст
                    if message.text or message.message:
                        await process_text_message(event.client, message)
                    else:
                        print(f"⏭️ Пропускаем документ (не видео): {mime_type}")
            else:
                # Другие типы медиа - пробуем обработать как текст
                if message.text or message.message:
                    await process_text_message(event.client, message)
                else:
                    print(f"ℹ️ Неизвестный тип медиа: {type(message.media)}")
        else:
            await process_text_message(event.client, message)
            
    except Exception as e:
        print(f"🔥 Ошибка в обработчике: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Основная функция бота"""
    print("🚀 Запуск основного цикла бота...")
    
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
        
        # Регистрируем обработчик для ВСЕХ сообщений
        client.add_event_handler(
            new_message_handler,
            events.NewMessage(chats=SOURCE_CHANNEL)
        )
        
        print(f"👂 Ожидание ВСЕХ новых сообщений из {SOURCE_CHANNEL}...")
        print(f"📤 Отправка в: {TARGET_CHANNEL}")
        print(f"🔗 Удаление абзацев со ссылками: ВКЛЮЧЕНО")
        print(f"📝 Подпись: 📰 Источник: ЦарьградТВ")
        print("=" * 70)
        print("✅ Бот успешно запущен!")
        print("=" * 70)
        
        # Бесконечный цикл
        await client.run_until_disconnected()
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("🔌 Завершение работы...")
        await client.disconnect()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Бот остановлен")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        sys.exit(1)
