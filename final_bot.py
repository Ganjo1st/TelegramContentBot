# final_bot.py - Финальная рабочая версия
import asyncio
import os
import re
from datetime import datetime
from telethon import TelegramClient, events
from telegram import Bot

print("=" * 60)
print("🤖 TELEGRAM CONTENT BOT - ФИНАЛЬНАЯ ВЕРСИЯ")
print("=" * 60)

# Конфигурация
API_ID = 37267988
API_HASH = "0d6a0ea97840273b408297adf779ff80"
BOT_TOKEN = "8459279128:AAGsWSNhVNQH57NFignIpEDQ-PcipAxfD9Y"
SOURCE_CHANNEL = "@tsargradtv"
TARGET_CHANNEL = "@Chanal_in_1"


class FinalBot:
    def __init__(self):
        self.user_client = TelegramClient('user_session', API_ID, API_HASH)
        self.bot = Bot(token=BOT_TOKEN)
        self.processed_ids = self.load_ids()

    def load_ids(self):
        """Загружает обработанные ID"""
        if os.path.exists('processed.txt'):
            with open('processed.txt', 'r', encoding='utf-8') as f:
                return set(line.strip() for line in f)
        return set()

    def save_id(self, post_id):
        """Сохраняет ID"""
        with open('processed.txt', 'a', encoding='utf-8') as f:
            f.write(f"{post_id}\n")
        self.processed_ids.add(post_id)

    def clean_text(self, text):
        """Очищает текст от всех ссылок и рекламы"""
        if not text:
            return '<a href="https://t.me/tsargradtv">ЦарьградТВ</a>'

        # Удаляем строки с ссылками
        lines = text.split('\n')
        clean_lines = []

        for line in lines:
            # Пропускаем строки с ссылками и рекламой
            if re.search(r'https?://|t\.me/|@\w+', line):
                continue
            if re.search(r'Подписывайтесь|Подпишись|Читайте также|Смотрите также', line, re.IGNORECASE):
                continue
            if re.search(r'🤴\s*\[\*\*Царьград\.ТВ|Царьград\.ТВ\s*—', line):
                continue

            if line.strip():
                clean_lines.append(line.strip())

        # Объединяем
        result = '\n'.join(clean_lines)

        # Удаляем оставшиеся ссылки
        result = re.sub(r'https?://\S+', '', result)
        result = re.sub(r't\.me/\S+', '', result)
        result = re.sub(r'@\w+', '', result)

        # Очищаем
        result = re.sub(r'\n{3,}', '\n\n', result)
        result = result.strip()

        # Добавляем ссылку
        if result:
            return f"{result}\n\n<a href=\"https://t.me/tsargradtv\">ЦарьградТВ</a>"
        return '<a href="https://t.me/tsargradtv">ЦарьградТВ</a>'

    async def process_post(self, message):
        """Обрабатывает пост"""
        try:
            msg_id = str(message.id)

            if msg_id in self.processed_ids:
                return

            print(f"\n🔄 Обработка поста {msg_id}")

            # Текст
            text = message.text or message.message or ""
            cleaned = self.clean_text(text)

            # Медиа
            if message.media:
                os.makedirs('temp', exist_ok=True)
                filename = f"temp/{msg_id}"

                await message.download_media(file=filename)

                # Находим фактический файл
                actual_file = None
                for f in os.listdir('temp'):
                    if f.startswith(msg_id):
                        actual_file = f"temp/{f}"
                        break

                if actual_file and os.path.exists(actual_file):
                    ext = os.path.splitext(actual_file)[1].lower()

                    with open(actual_file, 'rb') as f:
                        if ext in ['.mp4', '.avi', '.mov']:
                            await self.bot.send_video(
                                chat_id=TARGET_CHANNEL,
                                video=f,
                                caption=cleaned,
                                parse_mode='HTML'
                            )
                        elif ext in ['.jpg', '.jpeg', '.png']:
                            await self.bot.send_photo(
                                chat_id=TARGET_CHANNEL,
                                photo=f,
                                caption=cleaned,
                                parse_mode='HTML'
                            )

                    # Удаляем файл
                    os.remove(actual_file)
            else:
                # Только текст
                await self.bot.send_message(
                    chat_id=TARGET_CHANNEL,
                    text=cleaned,
                    parse_mode='HTML'
                )

            # Сохраняем ID
            self.save_id(msg_id)
            print(f"✅ Отправлено в {TARGET_CHANNEL}")

        except Exception as e:
            print(f"❌ Ошибка: {e}")

    async def check_recent(self):
        """Проверяет последние посты"""
        try:
            channel = await self.user_client.get_entity(SOURCE_CHANNEL)
            print(f"\n📺 Канал: {channel.title}")
            print("🔍 Проверка последних 5 постов...")

            messages = []
            async for msg in self.user_client.iter_messages(channel, limit=5):
                messages.append(msg)

            for msg in reversed(messages):
                await self.process_post(msg)
                await asyncio.sleep(1)

        except Exception as e:
            print(f"❌ Ошибка проверки: {e}")

    async def run(self):
        """Запускает бота"""
        try:
            # Подключаем user-клиент
            await self.user_client.connect()

            if not await self.user_client.is_user_authorized():
                print("❌ User-клиент не авторизован")
                return

            print("✅ User-клиент авторизован")

            # Проверяем бота
            bot_info = await self.bot.get_me()
            print(f"✅ Бот: @{bot_info.username}")

            # Проверяем последние посты
            await self.check_recent()

            # Настраиваем обработчик
            channel = await self.user_client.get_entity(SOURCE_CHANNEL)

            @self.user_client.on(events.NewMessage(chats=channel))
            async def handler(event):
                print(f"\n📨 НОВЫЙ ПОСТ! (ID: {event.message.id})")
                await self.process_post(event.message)

            print("\n" + "=" * 60)
            print("✅ БОТ ЗАПУЩЕН И РАБОТАЕТ")
            print("=" * 60)
            print(f"📡 Мониторинг: {SOURCE_CHANNEL}")
            print(f"📤 Отправка в: {TARGET_CHANNEL}")
            print("🛑 Ctrl+C для остановки")
            print("=" * 60 + "\n")

            # Ожидаем
            await self.user_client.run_until_disconnected()

        except KeyboardInterrupt:
            print("\n🛑 Остановлено")
        except Exception as e:
            print(f"\n💥 Ошибка: {e}")
        finally:
            if self.user_client.is_connected():
                await self.user_client.disconnect()


async def main():
    bot = FinalBot()
    await bot.run()


if __name__ == "__main__":
    asyncio.run(main())