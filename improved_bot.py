# improved_bot.py - Улучшенный бот с обработкой ошибок
import asyncio
import os
import re
import json
import time
from datetime import datetime, timedelta
from telethon import TelegramClient, events
from telegram import Bot
from telegram.error import TelegramError, RetryAfter

print("=" * 70)
print("🤖 УЛУЧШЕННЫЙ TELEGRAM БОТ")
print("=" * 70)

# Конфигурация
API_ID = 37267988
API_HASH = "0d6a0ea97840273b408297adf779ff80"
BOT_TOKEN = "8459279128:AAGsWSNhVNQH57NFignIpEDQ-PcipAxfD9Y"
SOURCE_CHANNEL = "@tsargradtv"
TARGET_CHANNEL = "@Chanal_in_1"


class ImprovedBot:
    def __init__(self):
        self.user_client = TelegramClient('user_session', API_ID, API_HASH)
        self.bot = Bot(token=BOT_TOKEN)

        # Статистика
        self.stats = {
            'total_sent': 0,
            'today_sent': 0,
            'errors': 0,
            'start_time': datetime.now()
        }

        # Загружаем данные
        self.load_data()

    def load_data(self):
        """Загружает данные"""
        # Обработанные ID
        self.processed_ids = set()
        if os.path.exists('processed_ids.json'):
            try:
                with open('processed_ids.json', 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.processed_ids = set(data.get('ids', []))
                    self.stats = data.get('stats', self.stats)
                print(f"📂 Загружено {len(self.processed_ids)} ID")
            except:
                pass

        # Создаем папки
        os.makedirs('temp', exist_ok=True)
        os.makedirs('backup', exist_ok=True)

    def save_data(self):
        """Сохраняет данные"""
        try:
            data = {
                'ids': list(self.processed_ids),
                'stats': self.stats,
                'last_save': datetime.now().isoformat()
            }
            with open('processed_ids.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            # Бекап
            backup_file = f"backup/processed_{int(time.time())}.json"
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            print(f"⚠ Ошибка сохранения: {e}")

    def clean_text(self, text):
        """Очищает текст"""
        if not text:
            return '<a href="https://t.me/tsargradtv">ЦарьградТВ</a>'

        # Удаляем строки с ссылками
        lines = text.split('\n')
        clean_lines = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Пропускаем строки с ссылками
            if re.search(r'https?://|t\.me/|@\w+', line):
                continue

            # Пропускаем рекламу
            if re.search(r'Подписывайтесь|Подпишись|Читайте также|Смотрите также', line, re.IGNORECASE):
                continue

            # Пропускаем шапку канала
            if re.search(r'🤴\s*\[\*\*Царьград\.ТВ|Царьград\.ТВ\s*—', line):
                continue

            # Удаляем хештеги в конце строки
            line = re.sub(r'#\w+\s*$', '', line)

            if line:
                clean_lines.append(line)

        # Объединяем
        result = '\n'.join(clean_lines)

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

    async def safe_send(self, text, media_path=None, retry_count=3):
        """Безопасная отправка с повторами"""
        for attempt in range(retry_count):
            try:
                if media_path and os.path.exists(media_path):
                    ext = os.path.splitext(media_path)[1].lower()

                    with open(media_path, 'rb') as file:
                        if ext in ['.mp4', '.avi', '.mov', '.mkv', '.webm']:
                            await self.bot.send_video(
                                chat_id=TARGET_CHANNEL,
                                video=file,
                                caption=text,
                                parse_mode='HTML',
                                supports_streaming=True,
                                read_timeout=60,
                                write_timeout=60,
                                connect_timeout=60
                            )
                        elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
                            await self.bot.send_photo(
                                chat_id=TARGET_CHANNEL,
                                photo=file,
                                caption=text,
                                parse_mode='HTML',
                                read_timeout=60,
                                write_timeout=60,
                                connect_timeout=60
                            )
                        else:
                            await self.bot.send_document(
                                chat_id=TARGET_CHANNEL,
                                document=file,
                                caption=text,
                                parse_mode='HTML',
                                read_timeout=60,
                                write_timeout=60,
                                connect_timeout=60
                            )
                else:
                    await self.bot.send_message(
                        chat_id=TARGET_CHANNEL,
                        text=text,
                        parse_mode='HTML',
                        read_timeout=60,
                        write_timeout=60,
                        connect_timeout=60
                    )

                return True

            except RetryAfter as e:
                wait_time = e.retry_after
                print(f"⏳ Telegram просит подождать {wait_time} секунд")
                await asyncio.sleep(wait_time + 2)
                continue

            except TelegramError as e:
                print(f"⚠ Ошибка Telegram (попытка {attempt + 1}/{retry_count}): {e}")
                if attempt < retry_count - 1:
                    await asyncio.sleep(5 * (attempt + 1))
                continue

            except Exception as e:
                print(f"⚠ Общая ошибка (попытка {attempt + 1}/{retry_count}): {e}")
                if attempt < retry_count - 1:
                    await asyncio.sleep(5 * (attempt + 1))
                continue

        return False

    async def process_post(self, message, is_new=True):
        """Обрабатывает пост"""
        try:
            msg_id = str(message.id)

            # Проверяем, не обрабатывали ли уже
            if msg_id in self.processed_ids:
                if is_new:
                    print(f"⏭ Пропускаем уже обработанный пост {msg_id}")
                return False

            prefix = "🆕" if is_new else "🔄"
            print(f"\n{prefix} Обработка поста {msg_id}")

            # Текст
            text = message.text or message.message or ""
            cleaned_text = self.clean_text(text)

            print(f"📝 Текст: {len(cleaned_text)} символов")

            # Скачиваем медиа
            media_path = None
            if message.media:
                try:
                    os.makedirs('temp', exist_ok=True)
                    timestamp = int(time.time())
                    filename = f"temp/{msg_id}_{timestamp}"

                    # Скачиваем с прогрессом
                    print("📥 Скачивание медиа...")
                    await message.download_media(file=filename)

                    # Находим файл
                    for f in os.listdir('temp'):
                        if f.startswith(f"{msg_id}_{timestamp}"):
                            media_path = f"temp/{f}"
                            file_size = os.path.getsize(media_path) / 1024 / 1024
                            print(f"📁 Файл: {f} ({file_size:.1f} MB)")
                            break

                except Exception as e:
                    print(f"⚠ Ошибка скачивания медиа: {e}")
                    media_path = None

            # Отправляем
            print("📤 Отправка...")
            success = await self.safe_send(cleaned_text, media_path)

            # Удаляем временный файл
            if media_path and os.path.exists(media_path):
                try:
                    os.remove(media_path)
                except:
                    pass

            if success:
                # Сохраняем
                self.processed_ids.add(msg_id)
                self.stats['total_sent'] += 1
                self.stats['today_sent'] += 1

                # Сохраняем данные каждые 5 постов
                if self.stats['total_sent'] % 5 == 0:
                    self.save_data()

                print(f"✅ Успешно отправлено!")
                self.show_stats()
                return True
            else:
                self.stats['errors'] += 1
                print(f"❌ Не удалось отправить после нескольких попыток")
                return False

        except Exception as e:
            self.stats['errors'] += 1
            print(f"💥 Критическая ошибка обработки: {e}")
            return False

    def show_stats(self):
        """Показывает статистику"""
        uptime = datetime.now() - self.stats['start_time']
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        stats_text = f"""
📊 СТАТИСТИКА:
├ Всего отправлено: {self.stats['total_sent']}
├ Отправлено сегодня: {self.stats['today_sent']}
├ Ошибок: {self.stats['errors']}
├ В работе: {hours:02d}:{minutes:02d}:{seconds:02d}
└ Обработано ID: {len(self.processed_ids)}
"""
        print(stats_text)

    async def check_history(self, limit=20):
        """Проверяет историю сообщений"""
        try:
            print(f"\n🔍 Проверка истории ({limit} последних постов)...")

            channel = await self.user_client.get_entity(SOURCE_CHANNEL)
            print(f"📺 Канал: {channel.title}")

            # Собираем сообщения
            messages = []
            async for msg in self.user_client.iter_messages(channel, limit=limit):
                messages.append(msg)

            print(f"📊 Найдено {len(messages)} сообщений")

            # Обрабатываем от старых к новым
            to_process = []
            for msg in reversed(messages):
                msg_id = str(msg.id)
                if msg_id not in self.processed_ids:
                    to_process.append(msg)

            print(f"📋 Новых для обработки: {len(to_process)}")

            # Обрабатываем с паузами
            for i, msg in enumerate(to_process, 1):
                print(f"\n[{i}/{len(to_process)}] ", end="")
                await self.process_post(msg, is_new=False)
                await asyncio.sleep(3)  # Пауза между отправками

            # Сохраняем данные
            self.save_data()

        except Exception as e:
            print(f"❌ Ошибка проверки истории: {e}")

    async def run(self):
        """Запускает бота"""
        try:
            # Подключаемся
            await self.user_client.connect()

            if not await self.user_client.is_user_authorized():
                print("❌ User-клиент не авторизован")
                return

            print("✅ User-клиент авторизован")

            # Проверяем бота
            bot_info = await self.bot.get_me()
            print(f"✅ Бот: @{bot_info.username}")

            # Проверяем целевой канал
            try:
                target = await self.user_client.get_entity(TARGET_CHANNEL)
                print(f"✅ Целевой канал: {target.title}")
            except:
                print(f"📤 Целевой канал: {TARGET_CHANNEL}")

            # Показываем статистику
            self.show_stats()

            # Проверяем историю
            await self.check_history(limit=10)

            # Настраиваем обработчик
            channel = await self.user_client.get_entity(SOURCE_CHANNEL)

            @self.user_client.on(events.NewMessage(chats=channel))
            async def handler(event):
                print(f"\n{'=' * 40}")
                print("📨 НОВЫЙ ПОСТ В КАНАЛЕ!")
                print(f"{'=' * 40}")
                await self.process_post(event.message, is_new=True)
                self.save_data()

            print("\n" + "=" * 70)
            print("✅ БОТ УСПЕШНО ЗАПУЩЕН И РАБОТАЕТ")
            print("=" * 70)
            print(f"📡 Мониторинг: {SOURCE_CHANNEL}")
            print(f"📤 Отправка в: {TARGET_CHANNEL}")
            print(f"💾 Сохранено ID: {len(self.processed_ids)}")
            print("🛑 Для остановки нажмите Ctrl+C")
            print("=" * 70 + "\n")

            # Основной цикл
            while True:
                try:
                    # Каждый час сбрасываем счетчик дневных постов
                    now = datetime.now()
                    if now.hour == 0 and now.minute == 0:
                        self.stats['today_sent'] = 0
                        print("🔄 Сброшен счетчик дневных постов")

                    # Каждые 30 минут сохраняем данные
                    if now.minute % 30 == 0:
                        self.save_data()
                        print("💾 Автосохранение данных")

                    # Ждем
                    await asyncio.sleep(60)

                except KeyboardInterrupt:
                    break
                except Exception as e:
                    print(f"⚠ Ошибка в основном цикле: {e}")
                    await asyncio.sleep(60)

        except KeyboardInterrupt:
            print("\n\n🛑 Остановлено пользователем")
        except Exception as e:
            print(f"\n💥 Критическая ошибка: {e}")
        finally:
            # Сохраняем данные
            self.save_data()

            # Корректное завершение
            if self.user_client.is_connected():
                await self.user_client.disconnect()

            print("\n" + "=" * 70)
            print("👋 БОТ ОСТАНОВЛЕН")
            self.show_stats()
            print("=" * 70)


async def main():
    bot = ImprovedBot()
    await bot.run()


if __name__ == "__main__":
    # Очищаем старые временные файлы
    if os.path.exists('temp'):
        for file in os.listdir('temp'):
            try:
                file_path = os.path.join('temp', file)
                # Удаляем файлы старше 1 часа
                if os.path.getmtime(file_path) < time.time() - 3600:
                    os.remove(file_path)
            except:
                pass

    # Запускаем
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Программа завершена")