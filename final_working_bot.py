# final_working_bot.py - Финальная рабочая версия
import asyncio
import os
import re
import json
import time
from datetime import datetime
from telethon import TelegramClient, events
from telegram import Bot
from telegram.request import HTTPXRequest

print("=" * 70)
print("🤖 FINAL TELEGRAM CONTENT BOT")
print("=" * 70)

# Конфигурация
API_ID = 37267988
API_HASH = "0d6a0ea97840273b408297adf779ff80"
BOT_TOKEN = "8459279128:AAGsWSNhVNQH57NFignIpEDQ-PcipAxfD9Y"
SOURCE_CHANNEL = "@tsargradtv"
TARGET_CHANNEL = "@Chanal_in_1"


class FinalBot:
    def __init__(self):
        # User-клиент для чтения
        self.user_client = TelegramClient('user_session', API_ID, API_HASH)

        # Бот для отправки с увеличенными таймаутами
        request = HTTPXRequest(connect_timeout=60, read_timeout=60, write_timeout=60)
        self.bot = Bot(token=BOT_TOKEN, request=request)

        # Настройки
        self.skip_videos = True  # Пропускать видео (из-за таймаутов)
        self.process_photos = True  # Обрабатывать фото
        self.max_retries = 3  # Максимум попыток

        # Данные
        self.processed_ids = self.load_processed_ids()
        self.stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'skipped': 0,
            'started': datetime.now().isoformat()
        }

        print(f"📊 Загружено {len(self.processed_ids)} обработанных ID")

    def load_processed_ids(self):
        """Загружает обработанные ID"""
        if os.path.exists('final_processed.json'):
            try:
                with open('final_processed.json', 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if 'ids' in data:
                        return set(data['ids'])
            except:
                pass
        return set()

    def save_processed_ids(self):
        """Сохраняет обработанные ID"""
        try:
            data = {
                'ids': list(self.processed_ids),
                'stats': self.stats,
                'last_update': datetime.now().isoformat(),
                'total_count': len(self.processed_ids)
            }
            with open('final_processed.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠ Ошибка сохранения: {e}")

    def clean_text_pro(self, text):
        """Профессиональная очистка текста"""
        if not text:
            return '<a href="https://t.me/tsargradtv">ЦарьградТВ</a>'

        # Удаляем всё что содержит ссылки
        lines = text.split('\n')
        clean_lines = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Пропускаем если есть признаки рекламы/ссылок
            skip_patterns = [
                r'https?://',  # http/https ссылки
                r't\.me/',  # Telegram ссылки
                r'@\w+',  # Упоминания
                r'Подписывайтесь', r'Подпишись',
                r'Читайте также', r'Смотрите также',
                r'Источник:', r'Перейти:', r'Ссылка:',
                r'Рекомендуем:', r'Также читайте',
                r'Больше новостей', r'Читать далее',
                r'Смотреть далее', r'Подробнее',
                r'Официальный канал', r'Наш канал',
                r'Присоединяйтесь', r'Делитесь',
                r'Ставьте лайки', r'Комментируйте',
                r'🤴\s*\[\*\*Царьград\.ТВ',
                r'Царьград\.ТВ\s*—'
            ]

            skip = False
            for pattern in skip_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    skip = True
                    break

            if not skip and line:
                # Удаляем хештеги
                line = re.sub(r'#\w+\s*', '', line)
                clean_lines.append(line)

        # Объединяем
        result = '\n'.join(clean_lines)

        # Финальная очистка
        result = re.sub(r'https?://\S+', '', result)
        result = re.sub(r't\.me/\S+', '', result)
        result = re.sub(r'@\w+', '', result)
        result = re.sub(r'\n{3,}', '\n\n', result)
        result = result.strip()

        # Добавляем ссылку
        if result:
            return f"{result}\n\n<a href=\"https://t.me/tsargradtv\">ЦарьградТВ</a>"
        return '<a href="https://t.me/tsargradtv">ЦарьградТВ</a>'

    async def safe_download(self, message):
        """Безопасное скачивание медиа"""
        try:
            if not message.media:
                return None

            # Создаем папку
            os.makedirs('downloads', exist_ok=True)

            # Генерируем имя
            filename = f"downloads/{message.id}_{int(time.time())}"

            # Скачиваем
            await message.download_media(file=filename)

            # Находим файл
            for f in os.listdir('downloads'):
                if f.startswith(f"{message.id}_"):
                    filepath = f"downloads/{f}"
                    ext = os.path.splitext(filepath)[1].lower()

                    # Проверяем тип
                    if self.skip_videos and ext in ['.mp4', '.avi', '.mov', '.mkv']:
                        print(f"⏭ Пропущено видео")
                        os.remove(filepath)
                        return None

                    if not self.process_photos and ext in ['.jpg', '.jpeg', '.png']:
                        print(f"⏭ Пропущено фото")
                        os.remove(filepath)
                        return None

                    size = os.path.getsize(filepath) / 1024 / 1024
                    print(f"📥 Скачан {ext} ({size:.1f} MB)")
                    return filepath

            return None

        except Exception as e:
            print(f"⚠ Ошибка скачивания: {e}")
            return None

    async def send_post_safely(self, text, file_path=None):
        """Безопасная отправка поста"""
        for attempt in range(self.max_retries):
            try:
                if file_path and os.path.exists(file_path):
                    ext = os.path.splitext(file_path)[1].lower()

                    with open(file_path, 'rb') as f:
                        if ext in ['.jpg', '.jpeg', '.png']:
                            await self.bot.send_photo(
                                chat_id=TARGET_CHANNEL,
                                photo=f,
                                caption=text,
                                parse_mode='HTML'
                            )
                            return True
                        elif ext in ['.mp4', '.avi', '.mov'] and not self.skip_videos:
                            await self.bot.send_video(
                                chat_id=TARGET_CHANNEL,
                                video=f,
                                caption=text,
                                parse_mode='HTML'
                            )
                            return True
                        else:
                            # Для неизвестных типов или если пропускаем видео
                            await self.bot.send_message(
                                chat_id=TARGET_CHANNEL,
                                text=text,
                                parse_mode='HTML'
                            )
                            return True
                else:
                    # Только текст
                    await self.bot.send_message(
                        chat_id=TARGET_CHANNEL,
                        text=text,
                        parse_mode='HTML'
                    )
                    return True

            except Exception as e:
                print(f"⚠ Попытка {attempt + 1}/{self.max_retries} не удалась: {e}")
                if attempt < self.max_retries - 1:
                    wait = (attempt + 1) * 5
                    print(f"⏳ Жду {wait} секунд...")
                    await asyncio.sleep(wait)
                continue

        return False

    async def process_post(self, message, is_new=True):
        """Обрабатывает пост"""
        msg_id = str(message.id)

        # Проверяем
        if msg_id in self.processed_ids:
            print(f"⏭ Уже обработан: {msg_id}")
            self.stats['skipped'] += 1
            return False

        prefix = "🆕" if is_new else "🔍"
        print(f"\n{prefix} Пост {msg_id}")

        # Текст
        text = message.text or message.message or ""
        cleaned = self.clean_text_pro(text)
        print(f"📝 Текст: {len(cleaned)} симв.")

        # Медиа
        file_path = None
        if message.media and (self.process_photos or not self.skip_videos):
            file_path = await self.safe_download(message)

        # Отправляем
        print("📤 Отправка...")
        success = await self.send_post_safely(cleaned, file_path)

        # Убираем временный файл
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass

        # Обновляем статистику
        self.stats['total'] += 1

        if success:
            self.processed_ids.add(msg_id)
            self.stats['success'] += 1
            print("✅ Успешно")

            # Сохраняем каждые 3 успеха
            if self.stats['success'] % 3 == 0:
                self.save_processed_ids()
        else:
            self.stats['failed'] += 1
            print("❌ Не удалось")

        # Пауза
        await asyncio.sleep(2)
        return success

    def show_stats(self):
        """Показывает статистику"""
        print(f"""
📊 СТАТИСТИКА:
├ Всего попыток: {self.stats['total']}
├ Успешно: {self.stats['success']}
├ Ошибок: {self.stats['failed']}
├ Пропущено: {self.stats['skipped']}
└ Уникальных ID: {len(self.processed_ids)}
""")

    async def check_and_process_history(self):
        """Проверяет и обрабатывает историю"""
        try:
            print("\n🔍 Проверка истории...")

            # Подключаемся если не подключены
            if not self.user_client.is_connected():
                await self.user_client.connect()

            channel = await self.user_client.get_entity(SOURCE_CHANNEL)
            print(f"📺 Канал: {channel.title}")

            # Собираем последние сообщения
            messages = []
            async for msg in self.user_client.iter_messages(channel, limit=20):
                messages.append(msg)

            print(f"📊 Найдено: {len(messages)} сообщений")

            # Определяем новые
            new_msgs = [msg for msg in reversed(messages)
                        if str(msg.id) not in self.processed_ids]

            print(f"📋 Новых: {len(new_msgs)}")

            # Обрабатываем
            for i, msg in enumerate(new_msgs, 1):
                print(f"\n[{i}/{len(new_msgs)}] ", end="")
                await self.process_post(msg, is_new=False)
                if i % 5 == 0:  # Сохраняем каждые 5
                    self.save_processed_ids()

            # Финальное сохранение
            self.save_processed_ids()

        except Exception as e:
            print(f"❌ Ошибка: {e}")

    async def run(self):
        """Запускает бота"""
        print("\n⚙️ Настройки:")
        print(f"├ Пропускать видео: {'Да' if self.skip_videos else 'Нет'}")
        print(f"├ Обрабатывать фото: {'Да' if self.process_photos else 'Нет'}")
        print(f"└ Макс. попыток: {self.max_retries}")

        try:
            # Подключаем user-клиент
            await self.user_client.connect()

            if not await self.user_client.is_user_authorized():
                print("❌ User не авторизован")
                return

            print("✅ User-клиент авторизован")

            # Проверяем бота
            bot_info = await self.bot.get_me()
            print(f"✅ Бот: @{bot_info.username}")

            # Обрабатываем историю
            await self.check_and_process_history()

            # Показываем статистику
            self.show_stats()

            # Настраиваем обработчик новых сообщений
            channel = await self.user_client.get_entity(SOURCE_CHANNEL)

            @self.user_client.on(events.NewMessage(chats=channel))
            async def handler(event):
                print(f"\n{'=' * 40}")
                print("📨 НОВОЕ СООБЩЕНИЕ!")
                print(f"{'=' * 40}")
                await self.process_post(event.message)
                self.save_processed_ids()
                self.show_stats()

            print("\n" + "=" * 70)
            print("✅ БОТ ЗАПУЩЕН И РАБОТАЕТ")
            print("=" * 70)
            print(f"📡 Мониторинг: {SOURCE_CHANNEL}")
            print(f"📤 Отправка в: {TARGET_CHANNEL}")
            print("🛑 Ctrl+C для остановки")
            print("=" * 70 + "\n")

            # Основной цикл
            while True:
                try:
                    await asyncio.sleep(60)
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    print(f"⚠ Ошибка в цикле: {e}")
                    await asyncio.sleep(30)

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
    # Очищаем старые загрузки
    if os.path.exists('downloads'):
        for f in os.listdir('downloads'):
            try:
                filepath = os.path.join('downloads', f)
                # Удаляем файлы старше 1 часа
                if os.path.getmtime(filepath) < time.time() - 3600:
                    os.remove(filepath)
            except:
                pass

    # Запускаем
    bot = FinalBot()
    await bot.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Завершено")