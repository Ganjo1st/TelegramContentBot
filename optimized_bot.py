# optimized_bot.py - Оптимизированный бот для работы с Telegram
import asyncio
import os
import re
import json
import time
from datetime import datetime
from telethon import TelegramClient, events
from telegram import Bot
from telegram.error import TelegramError, RetryAfter

print("=" * 70)
print("🚀 ОПТИМИЗИРОВАННЫЙ TELEGRAM БОТ")
print("=" * 70)

# Конфигурация
API_ID = 37267988
API_HASH = "0d6a0ea97840273b408297adf779ff80"
BOT_TOKEN = "8459279128:AAGsWSNhVNQH57NFignIpEDQ-PcipAxfD9Y"
SOURCE_CHANNEL = "@tsargradtv"
TARGET_CHANNEL = "@Chanal_in_1"


class OptimizedBot:
    def __init__(self):
        self.user_client = TelegramClient('user_session', API_ID, API_HASH)
        self.bot = Bot(token=BOT_TOKEN, request_timeout=120)

        # Настройки
        self.max_file_size = 10 * 1024 * 1024  # 10 MB максимум
        self.skip_videos = True  # Пропускать видео
        self.send_text_only = False  # Отправлять только текст

        # Данные
        self.processed_ids = self.load_ids()
        self.stats = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'skipped': 0,
            'start_time': datetime.now()
        }

        print(f"📊 Загружено {len(self.processed_ids)} обработанных ID")

    def load_ids(self):
        """Загружает обработанные ID"""
        if os.path.exists('optimized_ids.json'):
            try:
                with open('optimized_ids.json', 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return set(data.get('ids', []))
            except:
                pass
        return set()

    def save_ids(self):
        """Сохраняет ID"""
        try:
            data = {
                'ids': list(self.processed_ids),
                'stats': self.stats,
                'last_update': datetime.now().isoformat()
            }
            with open('optimized_ids.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except:
            pass

    def clean_text_enhanced(self, text):
        """Улучшенная очистка текста"""
        if not text:
            return '<a href="https://t.me/tsargradtv">ЦарьградТВ</a>'

        # Разбиваем на строки
        lines = text.split('\n')
        cleaned_lines = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Пропускаем строки содержащие:
            # 1. Любые ссылки
            if re.search(r'https?://|t\.me/|@\w+', line):
                continue

            # 2. Рекламные фразы
            ad_phrases = [
                'Подписывайтесь', 'Подпишись', 'Читайте также',
                'Смотрите также', 'Источник:', 'Перейти:', 'Ссылка:',
                'Рекомендуем:', 'Также читайте', 'Больше новостей',
                'Читать далее', 'Смотреть далее', 'Подробнее',
                'Официальный канал', 'Наш канал', 'Присоединяйтесь'
            ]

            skip_line = False
            for phrase in ad_phrases:
                if phrase.lower() in line.lower():
                    skip_line = True
                    break

            if skip_line:
                continue

            # 3. Шапку канала
            if re.search(r'🤴\s*\[\*\*Царьград\.ТВ|Царьград\.ТВ\s*—', line):
                continue

            # 4. Хештеги в конце строки
            line = re.sub(r'#\w+\s*$', '', line).strip()

            if line:
                cleaned_lines.append(line)

        # Объединяем
        result = '\n'.join(cleaned_lines)

        # Удаляем одиночные ссылки
        result = re.sub(r'https?://\S+', '', result)
        result = re.sub(r't\.me/\S+', '', result)
        result = re.sub(r'@\w+', '', result)

        # Очищаем форматирование
        result = re.sub(r'\n{3,}', '\n\n', result)
        result = result.strip()

        # Добавляем ссылку
        if result:
            return f"{result}\n\n<a href=\"https://t.me/tsargradtv\">ЦарьградТВ</a>"
        return '<a href="https://t.me/tsargradtv">ЦарьградТВ</a>'

    async def download_media_safe(self, message):
        """Безопасное скачивание медиа"""
        try:
            if not message.media:
                return None

            # Создаем папку
            os.makedirs('temp_downloads', exist_ok=True)

            # Генерируем имя файла
            timestamp = int(time.time())
            filename = f"temp_downloads/{message.id}_{timestamp}"

            # Скачиваем
            await message.download_media(file=filename)

            # Находим фактический файл
            for f in os.listdir('temp_downloads'):
                if f.startswith(f"{message.id}_{timestamp}"):
                    filepath = f"temp_downloads/{f}"
                    file_size = os.path.getsize(filepath)

                    # Проверяем размер
                    if file_size > self.max_file_size:
                        print(f"⚠ Файл слишком большой: {file_size / 1024 / 1024:.1f} MB")
                        os.remove(filepath)
                        return None

                    # Проверяем тип
                    ext = os.path.splitext(filepath)[1].lower()

                    # Пропускаем видео если настроено
                    if self.skip_videos and ext in ['.mp4', '.avi', '.mov', '.mkv', '.webm']:
                        print(f"⏭ Пропущено видео: {ext}")
                        os.remove(filepath)
                        return None

                    print(f"📥 Скачан файл: {f} ({file_size / 1024 / 1024:.1f} MB)")
                    return filepath

            return None

        except Exception as e:
            print(f"⚠ Ошибка скачивания: {e}")
            return None

    async def send_with_retry(self, send_func, max_retries=2, delay=5):
        """Отправка с повторами"""
        for attempt in range(max_retries):
            try:
                await send_func()
                return True
            except RetryAfter as e:
                wait = e.retry_after
                print(f"⏳ Ожидание {wait} секунд...")
                await asyncio.sleep(wait + 2)
            except TelegramError as e:
                print(f"⚠ Ошибка Telegram (попытка {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(delay * (attempt + 1))
            except Exception as e:
                print(f"⚠ Ошибка (попытка {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(delay * (attempt + 1))

        return False

    async def send_media_post(self, text, media_path):
        """Отправка поста с медиа"""
        ext = os.path.splitext(media_path)[1].lower()

        async def send_photo():
            with open(media_path, 'rb') as f:
                await self.bot.send_photo(
                    chat_id=TARGET_CHANNEL,
                    photo=f,
                    caption=text,
                    parse_mode='HTML'
                )

        async def send_video():
            with open(media_path, 'rb') as f:
                await self.bot.send_video(
                    chat_id=TARGET_CHANNEL,
                    video=f,
                    caption=text,
                    parse_mode='HTML',
                    supports_streaming=True
                )

        async def send_document():
            with open(media_path, 'rb') as f:
                await self.bot.send_document(
                    chat_id=TARGET_CHANNEL,
                    document=f,
                    caption=text,
                    parse_mode='HTML'
                )

        if ext in ['.jpg', '.jpeg', '.png', '.gif']:
            return await self.send_with_retry(send_photo)
        elif ext in ['.mp4', '.avi', '.mov'] and not self.skip_videos:
            return await self.send_with_retry(send_video)
        else:
            return await self.send_with_retry(send_document)

    async def process_single_post(self, message, is_new=True):
        """Обрабатывает один пост"""
        msg_id = str(message.id)

        # Проверяем ID
        if msg_id in self.processed_ids:
            print(f"⏭ Пропущен (уже обработан): {msg_id}")
            self.stats['skipped'] += 1
            return False

        prefix = "🆕" if is_new else "🔄"
        print(f"\n{prefix} Пост {msg_id}")

        # Получаем текст
        text = message.text or message.message or ""
        cleaned_text = self.clean_text_enhanced(text)

        # Если только текст
        if self.send_text_only or not message.media:
            print("📝 Только текст")
            success = await self.send_with_retry(
                lambda: self.bot.send_message(
                    chat_id=TARGET_CHANNEL,
                    text=cleaned_text,
                    parse_mode='HTML'
                )
            )
        else:
            # С медиа
            print("🖼 С медиа")
            media_path = await self.download_media_safe(message)

            if media_path:
                success = await self.send_media_post(cleaned_text, media_path)
                # Удаляем файл
                try:
                    os.remove(media_path)
                except:
                    pass
            else:
                # Если не удалось скачать или пропустили - отправляем только текст
                print("📝 Отправляем только текст")
                success = await self.send_with_retry(
                    lambda: self.bot.send_message(
                        chat_id=TARGET_CHANNEL,
                        text=cleaned_text,
                        parse_mode='HTML'
                    )
                )

        # Обновляем статистику
        self.stats['total_processed'] += 1

        if success:
            self.processed_ids.add(msg_id)
            self.stats['successful'] += 1
            print(f"✅ Успешно")

            # Сохраняем каждые 5 успешных отправок
            if self.stats['successful'] % 5 == 0:
                self.save_ids()
        else:
            self.stats['failed'] += 1
            print(f"❌ Не удалось отправить")

        # Пауза между отправками
        await asyncio.sleep(3)

        return success

    def show_stats(self):
        """Показывает статистику"""
        uptime = datetime.now() - self.stats['start_time']
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        success_rate = 0
        if self.stats['total_processed'] > 0:
            success_rate = (self.stats['successful'] / self.stats['total_processed']) * 100

        print(f"""
📊 СТАТИСТИКА:
├ Обработано: {self.stats['total_processed']}
├ Успешно: {self.stats['successful']} ({success_rate:.1f}%)
├ Ошибок: {self.stats['failed']}
├ Пропущено: {self.stats['skipped']}
├ В работе: {hours:02d}:{minutes:02d}:{seconds:02d}
└ Уникальных ID: {len(self.processed_ids)}
""")

    async def process_history(self, limit=15):
        """Обрабатывает историю"""
        try:
            print(f"\n🔍 Обработка {limit} последних постов...")

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

            print(f"📋 Новых для обработки: {len(new_messages)}")

            # Обрабатываем
            for i, msg in enumerate(new_messages, 1):
                print(f"\n[{i}/{len(new_messages)}] ", end="")
                await self.process_single_post(msg, is_new=False)

            # Сохраняем
            self.save_ids()

        except Exception as e:
            print(f"❌ Ошибка обработки истории: {e}")

    async def run(self):
        """Запускает бота"""
        try:
            # Подключаемся
            await self.user_client.connect()

            if not await self.user_client.is_user_authorized():
                print("❌ Не авторизован")
                return

            print("✅ User-клиент авторизован")

            # Проверяем бота
            bot_info = await self.bot.get_me()
            print(f"✅ Бот: @{bot_info.username}")

            # Настройки
            print("\n⚙️ Настройки:")
            print(f"├ Макс. размер файла: {self.max_file_size / 1024 / 1024} MB")
            print(f"├ Пропускать видео: {'Да' if self.skip_videos else 'Нет'}")
            print(f"└ Только текст: {'Да' if self.send_text_only else 'Нет'}")

            # Обрабатываем историю
            await self.process_history(limit=15)

            # Показываем статистику
            self.show_stats()

            # Настраиваем обработчик
            channel = await self.user_client.get_entity(SOURCE_CHANNEL)

            @self.user_client.on(events.NewMessage(chats=channel))
            async def handler(event):
                print(f"\n{'=' * 40}")
                print("📨 НОВЫЙ ПОСТ!")
                print(f"{'=' * 40}")
                await self.process_single_post(event.message, is_new=True)
                self.save_ids()
                self.show_stats()

            print("\n" + "=" * 70)
            print("✅ БОТ ЗАПУЩЕН И РАБОТАЕТ")
            print("=" * 70)
            print(f"📡 Мониторинг: {SOURCE_CHANNEL}")
            print(f"📤 Отправка в: {TARGET_CHANNEL}")
            print("🛑 Для остановки нажмите Ctrl+C")
            print("=" * 70 + "\n")

            # Основной цикл
            while True:
                try:
                    await asyncio.sleep(60)
                except KeyboardInterrupt:
                    break

        except KeyboardInterrupt:
            print("\n\n🛑 Остановлено")
        except Exception as e:
            print(f"\n💥 Ошибка: {e}")
        finally:
            # Сохраняем
            self.save_ids()

            # Завершаем
            if self.user_client.is_connected():
                await self.user_client.disconnect()

            print("\n" + "=" * 70)
            print("👋 БОТ ОСТАНОВЛЕН")
            self.show_stats()
            print("=" * 70)


async def main():
    # Очищаем временные файлы
    if os.path.exists('temp_downloads'):
        for file in os.listdir('temp_downloads'):
            try:
                file_path = os.path.join('temp_downloads', file)
                if os.path.getmtime(file_path) < time.time() - 3600:
                    os.remove(file_path)
            except:
                pass

    # Запускаем
    bot = OptimizedBot()
    await bot.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Завершено")