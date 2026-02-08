# no_video_bot.py - Бот который пропускает посты с видео
import asyncio
import os
import re
import json
import time
from datetime import datetime
from telethon import TelegramClient, events
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument
from telegram import Bot
from telegram.request import HTTPXRequest

print("=" * 70)
print("🚫 TELEGRAM BOT - NO VIDEO COPY")
print("=" * 70)

# Конфигурация
API_ID = 37267988
API_HASH = "0d6a0ea97840273b408297adf779ff80"
BOT_TOKEN = "8459279128:AAGsWSNhVNQH57NFignIpEDQ-PcipAxfD9Y"
SOURCE_CHANNEL = "@tsargradtv"
TARGET_CHANNEL = "@Chanal_in_1"


class NoVideoBot:
    def __init__(self):
        # Клиенты
        self.user_client = TelegramClient('user_session', API_ID, API_HASH)
        request = HTTPXRequest(connect_timeout=30, read_timeout=30, write_timeout=30)
        self.bot = Bot(token=BOT_TOKEN, request=request)

        # Настройки
        self.skip_video_posts = True  # Пропускать посты с видео
        self.copy_photo_posts = True  # Копировать посты с фото
        self.copy_text_only = True  # Копировать текстовые посты

        # Данные
        self.processed_ids = self.load_processed_ids()
        self.stats = {
            'total_checked': 0,
            'copied': 0,
            'skipped_video': 0,
            'skipped_other': 0,
            'errors': 0,
            'started': datetime.now()
        }

        print(f"📊 Загружено {len(self.processed_ids)} обработанных ID")

    def load_processed_ids(self):
        """Загружает обработанные ID"""
        if os.path.exists('no_video_ids.json'):
            try:
                with open('no_video_ids.json', 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return set(data.get('ids', []))
            except:
                pass
        return set()

    def save_processed_ids(self):
        """Сохраняет обработанные ID"""
        try:
            data = {
                'ids': list(self.processed_ids),
                'stats': self.stats,
                'last_save': datetime.now().isoformat()
            }
            with open('no_video_ids.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except:
            pass

    def has_video(self, message):
        """Проверяет, содержит ли сообщение видео"""
        if not message.media:
            return False

        try:
            # Проверяем тип медиа
            if isinstance(message.media, MessageMediaDocument):
                document = message.media.document
                if hasattr(document, 'mime_type'):
                    # Проверяем MIME тип
                    if 'video' in document.mime_type:
                        return True

                # Проверяем атрибуты документа
                if hasattr(document, 'attributes'):
                    for attr in document.attributes:
                        # Если есть атрибут видео
                        if hasattr(attr, 'video'):
                            return True
                        # Проверяем по имени файла
                        if hasattr(attr, 'file_name'):
                            filename = attr.file_name.lower()
                            if any(ext in filename for ext in ['.mp4', '.avi', '.mov', '.mkv', '.webm']):
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
                    if 'image' in document.mime_type:
                        return True

                if hasattr(document, 'attributes'):
                    for attr in document.attributes:
                        if hasattr(attr, 'file_name'):
                            filename = attr.file_name.lower()
                            if any(ext in filename for ext in ['.jpg', '.jpeg', '.png', '.gif']):
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
            r'\d{1,2}:\d{2}.*',  # Время типа 2:46
        ]

        for pattern in ad_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)

        # 3. Фильтруем строки
        lines = text.split('\n')
        clean_lines = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Пропускаем строки с рекламными словами
            ad_words = ['подпис', 'читайте', 'смотрите', 'источник',
                        'перейти', 'ссылка', 'рекомендуем', 'больше',
                        'далее', 'подробнее', 'официальный', 'наш',
                        'присоединяйтесь', 'делитесь', 'редакция', 'реклама',
                        'вп', 'макс', 'телеграм', 'telegram', 'канал']

            line_lower = line.lower()
            has_ad_word = any(word in line_lower for word in ad_words)

            if not has_ad_word and len(line) > 3:
                clean_lines.append(line)

        # 4. Объединяем
        result = '\n'.join(clean_lines)

        # 5. Очищаем
        result = re.sub(r'\s+', ' ', result)
        result = re.sub(r'\n\s*\n+', '\n\n', result)
        result = result.strip()

        # 6. Добавляем ссылку
        if result:
            return f"{result}\n\n<a href=\"https://t.me/tsargradtv\">ЦарьградТВ</a>"
        return '<a href="https://t.me/tsargradtv">ЦарьградТВ</a>'

    async def download_photo(self, message):
        """Скачивает фото"""
        try:
            if not message.media:
                return None

            # Создаем папку
            os.makedirs('photos_temp', exist_ok=True)

            # Скачиваем
            filename = f"photos_temp/{message.id}_{int(time.time())}"
            await message.download_media(file=filename)

            # Находим файл
            for f in os.listdir('photos_temp'):
                if f.startswith(f"{message.id}_"):
                    filepath = f"photos_temp/{f}"
                    return filepath

            return None

        except:
            return None

    async def send_post(self, text, photo_path=None):
        """Отправляет пост"""
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

            return True

        except Exception as e:
            print(f"⚠ Ошибка отправки: {e}")
            return False

        finally:
            # Удаляем временный файл
            if photo_path and os.path.exists(photo_path):
                try:
                    os.remove(photo_path)
                except:
                    pass

    async def process_message(self, message):
        """Обрабатывает сообщение"""
        msg_id = str(message.id)
        self.stats['total_checked'] += 1

        # Проверяем, не обрабатывали ли уже
        if msg_id in self.processed_ids:
            return False

        print(f"\n🔍 Проверка поста {msg_id}")

        # 1. Проверяем видео
        if self.skip_video_posts and self.has_video(message):
            print("🚫 Пропущено (содержит видео)")
            self.stats['skipped_video'] += 1
            self.processed_ids.add(msg_id)  # Добавляем в обработанные чтобы не проверять снова
            self.save_processed_ids()
            return False

        # 2. Проверяем фото
        has_photo = self.has_photo(message)

        if not self.copy_photo_posts and has_photo:
            print("🚫 Пропущено (содержит фото)")
            self.stats['skipped_other'] += 1
            self.processed_ids.add(msg_id)
            self.save_processed_ids()
            return False

        # 3. Проверяем текст
        text = message.text or message.message or ""
        if not text.strip() and not has_photo:
            print("🚫 Пропущено (нет текста и не фото)")
            self.stats['skipped_other'] += 1
            self.processed_ids.add(msg_id)
            self.save_processed_ids()
            return False

        # 4. Если дошли сюда - обрабатываем
        print("✅ Подходит для копирования")

        # Очищаем текст
        cleaned_text = self.clean_text(text)

        # Скачиваем фото если есть
        photo_path = None
        if has_photo and self.copy_photo_posts:
            print("🖼 Скачиваю фото...")
            photo_path = await self.download_photo(message)

        # Отправляем
        print("📤 Отправляю...")
        success = await self.send_post(cleaned_text, photo_path)

        if success:
            self.processed_ids.add(msg_id)
            self.stats['copied'] += 1
            print("✅ Успешно скопировано")

            # Сохраняем каждые 3 поста
            if self.stats['copied'] % 3 == 0:
                self.save_processed_ids()
        else:
            self.stats['errors'] += 1
            print("❌ Ошибка копирования")

        # Пауза
        await asyncio.sleep(2)
        return success

    def show_stats(self):
        """Показывает статистику"""
        print(f"""
📊 СТАТИСТИКА:
├ Всего проверено: {self.stats['total_checked']}
├ Скопировано: {self.stats['copied']}
├ Пропущено видео: {self.stats['skipped_video']}
├ Пропущено других: {self.stats['skipped_other']}
├ Ошибок: {self.stats['errors']}
└ В обработке: {len(self.processed_ids)} ID
""")

    async def check_history(self, limit=30):
        """Проверяет историю сообщений"""
        try:
            print(f"\n🔍 Проверка {limit} последних постов...")

            channel = await self.user_client.get_entity(SOURCE_CHANNEL)
            print(f"📺 Канал: {channel.title}")

            # Собираем сообщения
            messages = []
            async for msg in self.user_client.iter_messages(channel, limit=limit):
                messages.append(msg)

            print(f"📊 Найдено: {len(messages)} сообщений")

            # Определяем новые
            new_messages = []
            for msg in reversed(messages):
                if str(msg.id) not in self.processed_ids:
                    new_messages.append(msg)

            print(f"📋 Новых для проверки: {len(new_messages)}")

            # Обрабатываем
            for i, msg in enumerate(new_messages, 1):
                print(f"\n[{i}/{len(new_messages)}] ", end="")
                await self.process_message(msg)

            # Сохраняем
            self.save_processed_ids()

        except Exception as e:
            print(f"❌ Ошибка проверки истории: {e}")

    async def run(self):
        """Запускает бота"""
        print("\n⚙️ Настройки:")
        print(f"├ Пропускать посты с видео: {'Да' if self.skip_video_posts else 'Нет'}")
        print(f"├ Копировать посты с фото: {'Да' if self.copy_photo_posts else 'Нет'}")
        print(f"└ Копировать текстовые посты: {'Да' if self.copy_text_only else 'Нет'}")

        try:
            # Подключаемся
            await self.user_client.connect()

            if not await self.user_client.is_user_authorized():
                print("❌ User не авторизован")
                return

            print("✅ User-клиент авторизован")

            # Проверяем бота
            bot_info = await self.bot.get_me()
            print(f"✅ Бот: @{bot_info.username}")

            # Проверяем историю
            await self.check_history(limit=30)

            # Показываем статистику
            self.show_stats()

            # Настраиваем обработчик
            channel = await self.user_client.get_entity(SOURCE_CHANNEL)

            @self.user_client.on(events.NewMessage(chats=channel))
            async def handler(event):
                print(f"\n{'=' * 40}")
                print("📨 НОВОЕ СООБЩЕНИЕ В КАНАЛЕ!")
                print(f"{'=' * 40}")
                await self.process_message(event.message)
                self.save_processed_ids()
                self.show_stats()

            print("\n" + "=" * 70)
            print("✅ БОТ ЗАПУЩЕН И РАБОТАЕТ")
            print("=" * 70)
            print(f"📡 Мониторинг: {SOURCE_CHANNEL}")
            print(f"📤 Отправка в: {TARGET_CHANNEL}")
            print("🚫 Посты с видео пропускаются")
            print("🛑 Ctrl+C для остановки")
            print("=" * 70 + "\n")

            # Основной цикл
            while True:
                try:
                    await asyncio.sleep(60)
                except KeyboardInterrupt:
                    break

        except KeyboardInterrupt:
            print("\n\n🛑 Остановлено пользователем")
        except Exception as e:
            print(f"\n💥 Критическая ошибка: {e}")
        finally:
            # Сохраняем данные
            self.save_processed_ids()

            # Отключаемся
            if self.user_client.is_connected():
                await self.user_client.disconnect()

            print("\n" + "=" * 70)
            print("👋 БОТ ОСТАНОВЛЕН")
            self.show_stats()
            print("=" * 70)


async def main():
    # Очищаем временные файлы
    if os.path.exists('photos_temp'):
        for f in os.listdir('photos_temp'):
            try:
                filepath = os.path.join('photos_temp', f)
                if os.path.getmtime(filepath) < time.time() - 3600:
                    os.remove(filepath)
            except:
                pass

    # Запускаем
    bot = NoVideoBot()
    await bot.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Завершено")