# no_video_bot.py - Полная версия для Railway со строковой сессией
import asyncio
import os
import re
import json
import time
import sys
from datetime import datetime
from telethon import TelegramClient, events
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument
from telethon.sessions import StringSession
from telegram import Bot
from telegram.request import HTTPXRequest
from aiohttp import web
import aiofiles

print("=" * 70)
print("🚫 TELEGRAM BOT - NO VIDEO COPY (Railway Cloud)")
print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)

# ===== КОНФИГУРАЦИЯ =====
API_ID = int(os.getenv('API_ID', '37267988'))
API_HASH = os.getenv('API_HASH', '0d6a0ea97840273b408297adf779ff80')
BOT_TOKEN = os.getenv('BOT_TOKEN', '8459279128:AAGsWSNhVNQH57NFignIpEDQ-PcipAxfD9Y')
SOURCE_CHANNEL = os.getenv('SOURCE_CHANNEL', '@tsargradtv')
TARGET_CHANNEL = os.getenv('TARGET_CHANNEL', '@Chanal_in_1')
SESSION_STRING = os.getenv('TELEGRAM_SESSION_STRING', '')

print(f"🔧 Режим: Railway Cloud")
print(f"📡 Канал-источник: {SOURCE_CHANNEL}")
print(f"📤 Ваш канал: {TARGET_CHANNEL}")
print(f"🔐 Сессия: {'✅ Найдена' if SESSION_STRING else '❌ Отсутствует'}")
print("=" * 70)


class NoVideoBot:
    def __init__(self):
        # Создаем сессию для Telegram
        if SESSION_STRING:
            # Используем строковую сессию из Railway
            session = StringSession(SESSION_STRING)
            print("✅ Используется строковая сессия из Railway")
        else:
            # Локальный режим - файловая сессия
            session = 'user_session'
            print("⚠ Используется локальная сессия (только для теста)")
        
        # Клиент Telegram
        self.user_client = TelegramClient(
            session,
            API_ID,
            API_HASH,
            device_model="Railway Cloud Bot",
            system_version="Linux",
            app_version="1.0",
            timeout=60,
            connection_retries=5
        )
        
        # Бот Telegram
        request = HTTPXRequest(
            connect_timeout=60,
            read_timeout=60,
            write_timeout=60
        )
        self.bot = Bot(token=BOT_TOKEN, request=request)

        # Настройки фильтрации
        self.skip_video_posts = True
        self.copy_photo_posts = True
        self.copy_text_only = True

        # Данные и статистика
        self.processed_ids = self.load_processed_ids()
        self.stats = {
            'total_checked': 0,
            'copied': 0,
            'skipped_video': 0,
            'skipped_other': 0,
            'errors': 0,
            'last_check': None,
            'started': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        print(f"📊 Загружено {len(self.processed_ids)} обработанных ID")

    def load_processed_ids(self):
        """Загружает обработанные ID из файла"""
        try:
            if os.path.exists('no_video_ids.json'):
                with open('no_video_ids.json', 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return set(data.get('ids', []))
        except Exception as e:
            print(f"⚠ Ошибка загрузки ID: {e}")
        
        return set()

    def save_processed_ids(self):
        """Сохраняет обработанные ID в файл"""
        try:
            data = {
                'ids': list(self.processed_ids),
                'stats': self.stats,
                'last_save': datetime.now().isoformat(),
                'total_count': len(self.processed_ids)
            }
            
            os.makedirs('data', exist_ok=True)
            
            with open('no_video_ids.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            print(f"💾 Данные сохранены ({len(self.processed_ids)} ID)")
            
        except Exception as e:
            print(f"⚠ Ошибка сохранения: {e}")

    def has_video(self, message):
        """Проверяет, содержит ли сообщение видео"""
        if not message.media:
            return False

        try:
            if isinstance(message.media, MessageMediaDocument):
                document = message.media.document
                
                if hasattr(document, 'mime_type'):
                    if 'video' in document.mime_type.lower():
                        return True

                if hasattr(document, 'attributes'):
                    for attr in document.attributes:
                        if hasattr(attr, 'video'):
                            return True
                        if hasattr(attr, 'file_name'):
                            filename = attr.file_name.lower()
                            video_exts = ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv']
                            if any(ext in filename for ext in video_exts):
                                return True

            return False

        except:
            return False

    def has_photo(self, message):
        """Проверяет, содержит ли сообщение фото"""
        if not message.media:
            return False

        try:
            if isinstance(message.media, MessageMediaPhoto):
                return True

            if isinstance(message.media, MessageMediaDocument):
                document = message.media.document
                
                if hasattr(document, 'mime_type'):
                    if 'image' in document.mime_type.lower():
                        return True

                if hasattr(document, 'attributes'):
                    for attr in document.attributes:
                        if hasattr(attr, 'file_name'):
                            filename = attr.file_name.lower()
                            image_exts = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
                            if any(ext in filename for ext in image_exts):
                                return True

            return False

        except:
            return False

    def clean_text(self, text):
        """Очищает текст от ссылок и рекламы"""
        if not text:
            return '<a href="https://t.me/tsargradtv">ЦарьградТВ</a>'

        # 1. Удаляем все ссылки
        text = re.sub(r'https?://\S+', '', text)
        text = re.sub(r't\.me/\S+', '', text)
        text = re.sub(r'@\w+', '', text)
        text = re.sub(r'www\.\S+', '', text)

        # 2. Удаляем рекламные блоки
        ad_patterns = [
            r'🤴\s*\[\*\*Царьград\.ТВ.*?\*\*\].*',
            r'Царьград\.ТВ\s*—\s*Не боимся говорить правду.*',
            r'Этот не покажут по телевизору.*',
            r'Честно обо всём происходящем в России и мире.*',
            r'Мы в Максе.*',
            r'Связаться с редакцией.*',
            r'Реклама и ВП.*',
            r'ПЕРЕЙТИ В КАНАЛ.*',
            r'Подписывайтесь.*',
            r'Подпишись.*',
            r'Читайте также.*',
            r'Смотрите также.*',
            r'Источник:.*',
            r'Перейти:.*',
            r'Ссылка:.*',
            r'Рекомендуем:.*',
            r'\d{1,2}:\d{2}.*',
        ]

        for pattern in ad_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)

        # 3. Фильтруем строки
        lines = text.split('\n')
        clean_lines = []

        for line in lines:
            line = line.strip()
            if not line or len(line) < 4:
                continue

            ad_words = [
                'подпис', 'читайте', 'смотрите', 'источник',
                'перейти', 'ссылка', 'рекомендуем', 'больше',
                'далее', 'подробнее', 'официальный', 'наш',
                'присоединяйтесь', 'делитесь', 'редакция', 'реклама',
                'вп', 'макс', 'телеграм', 'telegram', 'канал', 'бот'
            ]

            line_lower = line.lower()
            has_ad_word = any(word in line_lower for word in ad_words)

            if not has_ad_word:
                clean_lines.append(line)

        # 4. Объединяем и чистим
        if clean_lines:
            result = '\n'.join(clean_lines)
            result = re.sub(r'\s+', ' ', result)
            result = re.sub(r'\n\s*\n+', '\n\n', result)
            result = result.strip()
            
            if result:
                return f"{result}\n\n<a href=\"https://t.me/tsargradtv\">ЦарьградТВ</a>"
        
        return '<a href="https://t.me/tsargradtv">ЦарьградТВ</a>'

    async def download_photo(self, message):
        """Скачивает фото во временную папку"""
        try:
            if not message.media:
                return None

            os.makedirs('photos_temp', exist_ok=True)
            
            timestamp = int(time.time())
            filename = f"photos_temp/photo_{message.id}_{timestamp}"
            
            await message.download_media(file=filename)
            
            for f in os.listdir('photos_temp'):
                if f.startswith(f"photo_{message.id}_"):
                    filepath = os.path.join('photos_temp', f)
                    
                    if os.path.getsize(filepath) > 10240:
                        return filepath
                    else:
                        os.remove(filepath)
            
            return None

        except Exception as e:
            print(f"⚠ Ошибка скачивания фото: {e}")
            return None

    async def send_post(self, text, photo_path=None):
        """Отправляет пост в целевой канал"""
        try:
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    if photo_path and os.path.exists(photo_path):
                        with open(photo_path, 'rb') as f:
                            await self.bot.send_photo(
                                chat_id=TARGET_CHANNEL,
                                photo=f,
                                caption=text,
                                parse_mode='HTML'
                            )
                    else:
                        await self.bot.send_message(
                            chat_id=TARGET_CHANNEL,
                            text=text,
                            parse_mode='HTML'
                        )
                    
                    print(f"📤 Пост успешно отправлен (попытка {attempt + 1})")
                    return True
                    
                except Exception as e:
                    if attempt < max_retries - 1:
                        print(f"🔄 Повторная попытка отправки ({attempt + 1}/{max_retries})")
                        await asyncio.sleep(2)
                    else:
                        print(f"❌ Ошибка отправки после {max_retries} попыток: {e}")
                        return False
                        
        except Exception as e:
            print(f"⚠ Критическая ошибка отправки: {e}")
            return False
            
        finally:
            if photo_path and os.path.exists(photo_path):
                try:
                    os.remove(photo_path)
                except:
                    pass

    async def process_message(self, message):
        """Обрабатывает одно сообщение"""
        msg_id = str(message.id)
        self.stats['total_checked'] += 1

        if msg_id in self.processed_ids:
            return False

        print(f"\n🔍 Проверка поста #{msg_id}")

        # 1. Проверяем видео
        if self.skip_video_posts and self.has_video(message):
            print("🚫 Пропущено (содержит видео)")
            self.stats['skipped_video'] += 1
            self.processed_ids.add(msg_id)
            return False

        # 2. Проверяем фото
        has_photo = self.has_photo(message)
        
        if not self.copy_photo_posts and has_photo:
            print("🚫 Пропущено (содержит фото)")
            self.stats['skipped_other'] += 1
            self.processed_ids.add(msg_id)
            return False

        # 3. Проверяем текст
        text = message.text or message.message or ""
        if not text.strip() and not has_photo:
            print("🚫 Пропущено (нет текста и не фото)")
            self.stats['skipped_other'] += 1
            self.processed_ids.add(msg_id)
            return False

        # 4. Подходит для копирования
        print("✅ Подходит для копирования")
        
        cleaned_text = self.clean_text(text)

        photo_path = None
        if has_photo and self.copy_photo_posts:
            print("🖼 Скачиваю фото...")
            photo_path = await self.download_photo(message)

        print("📤 Отправляю...")
        success = await self.send_post(cleaned_text, photo_path)

        if success:
            self.processed_ids.add(msg_id)
            self.stats['copied'] += 1
            print("✅ Успешно скопировано")
        else:
            self.stats['errors'] += 1
            print("❌ Ошибка копирования")

        await asyncio.sleep(2)
        return success

    def show_stats(self):
        """Показывает статистику работы"""
        try:
            duration = datetime.now() - datetime.strptime(
                self.stats['started'], '%Y-%m-%d %H:%M:%S'
            )
            hours = int(duration.total_seconds() // 3600)
            minutes = int((duration.total_seconds() % 3600) // 60)
        except:
            hours, minutes = 0, 0
        
        print(f"""
📊 СТАТИСТИКА (работает {hours}ч {minutes}м):
├ Всего проверено: {self.stats['total_checked']}
├ Скопировано: {self.stats['copied']}
├ Пропущено видео: {self.stats['skipped_video']}
├ Пропущено других: {self.stats['skipped_other']}
├ Ошибок: {self.stats['errors']}
└ В обработке: {len(self.processed_ids)} ID
""")

    async def check_history(self, limit=30):
        """Проверяет историю сообщений в канале"""
        try:
            print(f"\n🔍 Проверка {limit} последних постов...")

            channel = await self.user_client.get_entity(SOURCE_CHANNEL)
            print(f"📺 Канал: {channel.title}")

            messages = []
            async for msg in self.user_client.iter_messages(channel, limit=limit):
                messages.append(msg)

            print(f"📊 Найдено: {len(messages)} сообщений")

            new_messages = []
            for msg in reversed(messages):
                if str(msg.id) not in self.processed_ids:
                    new_messages.append(msg)

            print(f"📋 Новых для обработки: {len(new_messages)}")

            for i, msg in enumerate(new_messages, 1):
                print(f"\n[{i}/{len(new_messages)}] ", end="")
                await self.process_message(msg)

            self.stats['last_check'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.save_processed_ids()

        except Exception as e:
            print(f"❌ Ошибка проверки истории: {e}")
            import traceback
            traceback.print_exc()

    async def start_health_check(self):
        """Запускает health check сервер для Railway"""
        try:
            async def health_handler(request):
                return web.Response(
                    text=f'✅ Telegram Bot is running\n'
                         f'Started: {self.stats["started"]}\n'
                         f'Checked: {self.stats["total_checked"]} posts\n'
                         f'Copied: {self.stats["copied"]} posts'
                )
            
            app = web.Application()
            app.router.add_get('/health', health_handler)
            
            runner = web.AppRunner(app)
            await runner.setup()
            
            site = web.TCPSite(runner, '0.0.0.0', 8000)
            await site.start()
            
            print("✅ Health check сервер запущен на порту 8000")
            print("🌐 Доступно по: http://0.0.0.0:8000/health")
            
            return runner
            
        except Exception as e:
            print(f"⚠ Health check не запущен: {e}")
            return None

    async def test_session(self):
        """Тестирует подключение сессии"""
        try:
            await self.user_client.connect()
            
            if await self.user_client.is_user_authorized():
                me = await self.user_client.get_me()
                print(f"✅ Сессия активна: {me.first_name} (@{me.username})")
                return True
            else:
                print("❌ Сессия не авторизована")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка тестирования сессии: {e}")
            return False
        finally:
            if self.user_client.is_connected():
                await self.user_client.disconnect()

    async def cloud_mode(self):
        """Режим работы для облака Railway"""
        print("\n☁️  ЗАПУСК В ОБЛАЧНОМ РЕЖИМЕ RAILWAY")
        print("⏱  Проверка каждые 5 минут...")
        print("=" * 70)
        
        health_runner = await self.start_health_check()
        
        check_count = 0
        while True:
            try:
                check_count += 1
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                print(f"\n{'='*50}")
                print(f"🔄 ПРОВЕРКА #{check_count} - {current_time}")
                print(f"{'='*50}")
                
                await self.check_history(limit=20)
                self.show_stats()
                self.save_processed_ids()
                
                print(f"\n⏳ Следующая проверка через 5 минут...")
                await asyncio.sleep(300)
                
            except KeyboardInterrupt:
                print("\n🛑 Получен сигнал остановки")
                break
            except Exception as e:
                print(f"\n⚠ Ошибка: {e}")
                await asyncio.sleep(60)
        
        if health_runner:
            await health_runner.cleanup()

    async def run(self):
        """Основной метод запуска"""
        print("\n⚙️ НАСТРОЙКИ ФИЛЬТРАЦИИ:")
        print(f"├ Пропускать посты с видео: {'✅ Да' if self.skip_video_posts else '❌ Нет'}")
        print(f"├ Копировать посты с фото: {'✅ Да' if self.copy_photo_posts else '❌ Нет'}")
        print(f"└ Копировать текстовые посты: {'✅ Да' if self.copy_text_only else '❌ Нет'}")
        print("=" * 70)
        
        # Тестируем сессию
        print("\n🔐 Тестирование сессии Telegram...")
        session_ok = await self.test_session()
        
        if not session_ok:
            print("\n❌ ПРОБЛЕМА С СЕССИЕЙ!")
            print("1. Запустите generate_session.py локально")
            print("2. Скопируйте строку сессии")
            print("3. Добавьте в Railway Variables как TELEGRAM_SESSION_STRING")
            return
        
        print("\n✅ Сессия работает! Запуск бота...")
        
        try:
            await self.user_client.connect()
            
            bot_info = await self.bot.get_me()
            print(f"✅ Бот: @{bot_info.username} (ID: {bot_info.id})")
            
            await self.cloud_mode()
                
        except KeyboardInterrupt:
            print("\n\n🛑 Остановлено пользователем")
        except Exception as e:
            print(f"\n💥 Критическая ошибка: {e}")
            import traceback
            traceback.print_exc()
        finally:
            print("\n💾 Сохранение данных...")
            self.save_processed_ids()
            
            if self.user_client.is_connected():
                await self.user_client.disconnect()
                print("🔌 Отключено от Telegram")
            
            print("\n" + "=" * 70)
            print("👋 БОТ ОСТАНОВЛЕН")
            self.show_stats()
            print("=" * 70)


async def cleanup_temp_files():
    """Очистка временных файлов"""
    try:
        if os.path.exists('photos_temp'):
            for filename in os.listdir('photos_temp'):
                filepath = os.path.join('photos_temp', filename)
                if os.path.getmtime(filepath) < time.time() - 3600:
                    os.remove(filepath)
                    
    except Exception as e:
        print(f"⚠ Ошибка очистки временных файлов: {e}")


async def main():
    """Точка входа"""
    await cleanup_temp_files()
    
    for folder in ['data', 'logs', 'photos_temp']:
        os.makedirs(folder, exist_ok=True)
    
    bot = NoVideoBot()
    await bot.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Программа завершена")
    except Exception as e:
        print(f"\n💥 Фатальная ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

# В конце no_video_bot.py добавьте:
async def main():
    # Ваш основной код запуска бота
    await client.start()
    # ... остальной код

if __name__ == "__main__":
    asyncio.run(main())

