# simple_bot.py - Упрощенный бот
import asyncio
import os
import re
import sys
from datetime import datetime
from telethon import TelegramClient, events
from telegram import Bot

# Конфигурация
API_ID = 37267988
API_HASH = "0d6a0ea97840273b408297adf779ff80"
BOT_TOKEN = "8459279128:AAGsWSNhVNQH57NFignIpEDQ-PcipAxfD9Y"
SOURCE_CHANNEL = "@tsargradtv"
TARGET_CHANNEL = "@Chanal_in_1"


class SimpleBot:
    def __init__(self):
        self.client = TelegramClient('session', API_ID, API_HASH)
        self.bot = Bot(token=BOT_TOKEN)
        self.processed = set()

    def clean_text(self, text):
        """Очищает текст"""
        if not text:
            return '<a href="https://t.me/tsargradtv">ЦарьградТВ</a>'

        # Удаляем строки с ссылками
        lines = text.split('\n')
        clean_lines = []
        for line in lines:
            if not re.search(r'https?://|t\.me/|@\w+', line):
                clean_lines.append(line)

        cleaned = '\n'.join(clean_lines)

        # Удаляем одиночные ссылки
        cleaned = re.sub(r'https?://\S+', '', cleaned)
        cleaned = re.sub(r't\.me/\S+', '', cleaned)
        cleaned = re.sub(r'@\w+', '', cleaned)

        # Удаляем рекламу
        ads = ['Подписывайтесь', 'Подпишись', 'Читайте также',
               'Смотрите также', 'Источник:', 'Перейти:', 'Ссылка:',
               'Рекомендуем:', 'Также читайте', 'Больше новостей']

        for ad in ads:
            cleaned = re.sub(f'{ad}.*', '', cleaned, flags=re.IGNORECASE)

        # Очищаем
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
        cleaned = cleaned.strip()

        # Добавляем ссылку
        if cleaned:
            return f"{cleaned}\n\n<a href=\"https://t.me/tsargradtv\">ЦарьградТВ</a>"
        return '<a href="https://t.me/tsargradtv">ЦарьградТВ</a>'

    async def process(self, message):
        """Обрабатывает сообщение"""
        try:
            msg_id = str(message.id)

            # Проверяем файл с обработанными ID
            if os.path.exists('processed.txt'):
                with open('processed.txt', 'r', encoding='utf-8') as f:
                    self.processed = set(line.strip() for line in f)

            if msg_id in self.processed:
                return

            print(f"\n📨 Новый пост: {msg_id}")

            # Текст
            text = message.text or message.message or ""
            cleaned = self.clean_text(text)

            # Медиа
            if message.media:
                os.makedirs('temp', exist_ok=True)
                filename = f"temp/{msg_id}"
                await message.download_media(file=filename)

                # Определяем тип
                if filename.endswith(('.mp4', '.avi', '.mov')):
                    with open(filename, 'rb') as f:
                        await self.bot.send_video(
                            chat_id=TARGET_CHANNEL,
                            video=f,
                            caption=cleaned,
                            parse_mode='HTML'
                        )
                elif filename.endswith(('.jpg', '.jpeg', '.png')):
                    with open(filename, 'rb') as f:
                        await self.bot.send_photo(
                            chat_id=TARGET_CHANNEL,
                            photo=f,
                            caption=cleaned,
                            parse_mode='HTML'
                        )

                # Удаляем файл
                if os.path.exists(filename):
                    os.remove(filename)
            else:
                # Только текст
                await self.bot.send_message(
                    chat_id=TARGET_CHANNEL,
                    text=cleaned,
                    parse_mode='HTML'
                )

            # Сохраняем ID
            with open('processed.txt', 'a', encoding='utf-8') as f:
                f.write(f"{msg_id}\n")

            print(f"✅ Отправлено в {TARGET_CHANNEL}")

        except Exception as e:
            print(f"❌ Ошибка: {e}")

    async def run(self):
        """Запускает бота"""
        print("=" * 50)
        print("🤖 ПРОСТОЙ ТЕЛЕГРАМ БОТ")
        print("=" * 50)

        try:
            # Подключаемся
            await self.client.start()
            print("✅ Подключено к Telegram")

            # Проверяем бота
            me = await self.bot.get_me()
            print(f"✅ Бот: @{me.username}")

            # Получаем канал
            channel = await self.client.get_entity(SOURCE_CHANNEL)
            print(f"✅ Канал: {channel.title}")

            # Проверяем последние 5 постов
            print("\n🔄 Проверяю последние посты...")
            messages = []
            async for msg in self.client.iter_messages(channel, limit=5):
                messages.append(msg)

            for msg in reversed(messages):
                await self.process(msg)
                await asyncio.sleep(1)

            # Настраиваем обработчик
            @self.client.on(events.NewMessage(chats=channel))
            async def handler(event):
                await self.process(event.message)

            print("\n" + "=" * 50)
            print("✅ БОТ ЗАПУЩЕН")
            print("=" * 50)
            print("📡 Ожидаю новые посты...")
            print("🛑 Ctrl+C для остановки")

            await self.client.run_until_disconnected()

        except KeyboardInterrupt:
            print("\n\n🛑 Остановлено")
        except Exception as e:
            print(f"\n💥 Ошибка: {e}")
        finally:
            if self.client.is_connected():
                await self.client.disconnect()


async def main():
    bot = SimpleBot()
    await bot.run()


if __name__ == "__main__":
    # Создаем папки
    for folder in ['temp']:
        os.makedirs(folder, exist_ok=True)

    asyncio.run(main())