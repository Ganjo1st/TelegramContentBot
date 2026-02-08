# working_bot.py - Рабочий бот с user-аккаунтом
import asyncio
import os
import re
import sys
from datetime import datetime
from telethon import TelegramClient, events
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument
from telegram import Bot

print("=" * 60)
print("🤖 TELEGRAM CONTENT BOT - НАСТРОЙКА")
print("=" * 60)

# Конфигурация
API_ID = 37267988
API_HASH = "0d6a0ea97840273b408297adf779ff80"
BOT_TOKEN = "8459279128:AAGsWSNhVNQH57NFignIpEDQ-PcipAxfD9Y"
SOURCE_CHANNEL = "@tsargradtv"
TARGET_CHANNEL = "@Chanal_in_1"


class WorkingBot:
    def __init__(self):
        # User-клиент для чтения (будет запрашивать номер телефона)
        self.user_client = TelegramClient(
            'user_session',
            API_ID,
            API_HASH,
            device_model="PC",
            system_version="Windows 10",
            app_version="1.0.0"
        )

        # Бот для отправки
        self.bot = Bot(token=BOT_TOKEN)

        # Загружаем обработанные ID
        self.processed_ids = self.load_processed_ids()

    def load_processed_ids(self):
        """Загружает обработанные ID"""
        try:
            if os.path.exists('processed_ids.txt'):
                with open('processed_ids.txt', 'r', encoding='utf-8') as f:
                    ids = set(line.strip() for line in f if line.strip())
                    print(f"📂 Загружено {len(ids)} обработанных ID")
                    return ids
            return set()
        except:
            return set()

    def save_processed_id(self, post_id):
        """Сохраняет ID"""
        try:
            with open('processed_ids.txt', 'a', encoding='utf-8') as f:
                f.write(f"{post_id}\n")
            self.processed_ids.add(post_id)
        except:
            pass

    def clean_text(self, text):
        """Очищает текст от ссылок и рекламы"""
        if not text:
            return '<a href="https://t.me/tsargradtv">ЦарьградТВ</a>'

        # Разделяем на строки
        lines = text.split('\n')
        clean_lines = []

        for line in lines:
            # Пропускаем строки, содержащие ссылки
            if re.search(r'https?://|t\.me/|@\w+|bit\.ly|t\.co|goo\.gl', line, re.IGNORECASE):
                continue

            # Пропускаем рекламные строки
            if re.search(r'Подписывайтесь|Подпишись|Читайте также|Смотрите также|Источник:|Перейти:|Ссылка:', line,
                         re.IGNORECASE):
                continue

            # Пропускаем шапку канала
            if re.search(r'🤴\s*\[\*\*Царьград\.ТВ|Царьград\.ТВ\s*—', line):
                continue

            # Добавляем чистую строку
            if line.strip():
                clean_lines.append(line.strip())

        # Объединяем обратно
        cleaned = '\n'.join(clean_lines)

        # Удаляем одиночные ссылки, которые могли остаться
        cleaned = re.sub(r'https?://\S+', '', cleaned)
        cleaned = re.sub(r't\.me/\S+', '', cleaned)
        cleaned = re.sub(r'@\w+', '', cleaned)

        # Очищаем форматирование
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
        cleaned = cleaned.strip()

        # Добавляем ссылку на источник
        if cleaned:
            return f"{cleaned}\n\n<a href=\"https://t.me/tsargradtv\">ЦарьградТВ</a>"
        else:
            return '<a href="https://t.me/tsargradtv">ЦарьградТВ</a>'

    async def download_media(self, message):
        """Скачивает медиа файл"""
        try:
            if not message.media:
                return None

            # Создаем папку для временных файлов
            os.makedirs("temp", exist_ok=True)

            # Генерируем уникальное имя файла
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"temp/media_{message.id}_{timestamp}"

            # Скачиваем файл
            await message.download_media(file=filename)
            print(f"📥 Скачан файл: {filename}")

            # Добавляем расширение
            actual_file = None
            for f in os.listdir("temp"):
                if f.startswith(f"media_{message.id}_{timestamp}"):
                    actual_file = f"temp/{f}"
                    break

            return actual_file

        except Exception as e:
            print(f"❌ Ошибка скачивания медиа: {e}")
            return None

    async def send_post(self, text, media_path=None):
        """Отправляет пост в целевой канал"""
        try:
            if media_path and os.path.exists(media_path):
                # Определяем тип файла
                ext = os.path.splitext(media_path)[1].lower()

                with open(media_path, 'rb') as file:
                    if ext in ['.mp4', '.avi', '.mov', '.mkv', '.webm']:
                        await self.bot.send_video(
                            chat_id=TARGET_CHANNEL,
                            video=file,
                            caption=text,
                            parse_mode='HTML',
                            supports_streaming=True
                        )
                        print("📹 Отправлено видео")

                    elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
                        await self.bot.send_photo(
                            chat_id=TARGET_CHANNEL,
                            photo=file,
                            caption=text,
                            parse_mode='HTML'
                        )
                        print("🖼 Отправлено фото")

                    else:
                        await self.bot.send_document(
                            chat_id=TARGET_CHANNEL,
                            document=file,
                            caption=text,
                            parse_mode='HTML'
                        )
                        print("📎 Отправлен документ")
            else:
                # Только текст
                await self.bot.send_message(
                    chat_id=TARGET_CHANNEL,
                    text=text,
                    parse_mode='HTML'
                )
                print("📝 Отправлен текст")

            return True

        except Exception as e:
            print(f"❌ Ошибка отправки: {e}")
            return False
        finally:
            # Удаляем временный файл
            if media_path and os.path.exists(media_path):
                try:
                    os.remove(media_path)
                except:
                    pass

    async def process_message(self, message):
        """Обрабатывает одно сообщение"""
        try:
            msg_id = str(message.id)

            # Проверяем, не обрабатывали ли уже
            if msg_id in self.processed_ids:
                return False

            print(f"\n🔧 Обработка сообщения ID: {msg_id}")

            # Получаем текст
            text = message.text or message.message or ""

            # Очищаем текст
            cleaned_text = self.clean_text(text)
            print(f"📄 Текст очищен ({len(cleaned_text)} символов)")

            # Скачиваем медиа (если есть)
            media_path = None
            if message.media:
                media_path = await self.download_media(message)

            # Отправляем в канал
            success = await self.send_post(cleaned_text, media_path)

            if success:
                # Сохраняем ID
                self.save_processed_id(msg_id)
                print(f"✅ Успешно отправлено!")
                return True
            else:
                print(f"❌ Ошибка отправки")
                return False

        except Exception as e:
            print(f"💥 Ошибка обработки: {e}")
            return False

    async def check_recent_posts(self):
        """Проверяет последние сообщения в канале"""
        try:
            print("\n🔍 Проверка последних постов...")

            # Получаем сущность канала
            entity = await self.user_client.get_entity(SOURCE_CHANNEL)
            print(f"📺 Канал: {entity.title}")

            # Получаем последние сообщения
            messages = []
            async for message in self.user_client.iter_messages(entity, limit=5):
                messages.append(message)

            print(f"📊 Найдено {len(messages)} сообщений")

            # Обрабатываем в правильном порядке (от старых к новым)
            for message in reversed(messages):
                await self.process_message(message)
                await asyncio.sleep(2)  # Пауза между отправками

        except Exception as e:
            print(f"❌ Ошибка при проверке: {e}")

    async def setup_user_client(self):
        """Настраивает user-клиент"""
        try:
            print("\n" + "=" * 50)
            print("📱 НАСТРОЙКА USER-КЛИЕНТА")
            print("=" * 50)
            print("Для чтения канала @tsargradtv нужен user-аккаунт.")
            print("Используйте номер телефона, а не токен бота!")
            print("=" * 50)

            # Подключаемся
            await self.user_client.connect()

            # Если уже авторизован
            if await self.user_client.is_user_authorized():
                print("✅ Используем сохраненную сессию")
                return True

            print("\n📞 Введите номер телефона:")
            print("Пример: +79161234567")
            phone = input("Номер: ").strip()

            # Отправляем запрос на код
            print("\n📨 Отправляю запрос на код...")
            await self.user_client.send_code_request(phone)

            print("\n✅ Запрос отправлен!")
            print("Код должен прийти в приложение Telegram на вашем телефоне.")
            print("Если код не приходит:")
            print("1. Проверьте приложение Telegram")
            print("2. Подождите 1-2 минуты")
            print("3. Убедитесь, что номер введен правильно")

            code = input("\n✍️ Введите код из Telegram: ").strip()

            # Пробуем войти
            try:
                await self.user_client.sign_in(phone, code)
                print("✅ Авторизация успешна!")
                return True
            except Exception as e:
                if "password" in str(e):
                    print("\n🔐 Требуется пароль 2FA")
                    password = input("Введите пароль: ").strip()
                    await self.user_client.sign_in(password=password)
                    print("✅ Авторизация с паролем успешна!")
                    return True
                else:
                    raise e

        except Exception as e:
            print(f"\n❌ Ошибка настройки: {e}")
            return False

    async def run(self):
        """Запускает бота"""
        print("\n" + "=" * 60)
        print("🚀 ЗАПУСК БОТА")
        print("=" * 60)

        try:
            # Настраиваем user-клиент
            if not await self.setup_user_client():
                print("❌ Не удалось настроить user-клиент")
                return

            # Проверяем бота
            bot_info = await self.bot.get_me()
            print(f"\n🤖 Бот: @{bot_info.username}")

            # Получаем информацию о каналах
            source_entity = await self.user_client.get_entity(SOURCE_CHANNEL)
            print(f"📺 Источник: {source_entity.title}")

            # Первоначальная проверка
            await self.check_recent_posts()

            # Настраиваем обработчик новых сообщений
            @self.user_client.on(events.NewMessage(chats=source_entity))
            async def new_message_handler(event):
                """Обработчик новых сообщений"""
                print(f"\n📨 НОВОЕ СООБЩЕНИЕ В КАНАЛЕ!")
                print(f"   ID: {event.message.id}")
                print(f"   Время: {datetime.now().strftime('%H:%M:%S')}")

                await self.process_message(event.message)

            print("\n" + "=" * 60)
            print("✅ БОТ УСПЕШНО ЗАПУЩЕН")
            print("=" * 60)
            print("📡 Ожидание новых сообщений из @tsargradtv...")
            print("📤 Автоматическая отправка в @Chanal_in_1")
            print("🛑 Для остановки нажмите Ctrl+C")
            print("=" * 60 + "\n")

            # Запускаем ожидание
            await self.user_client.run_until_disconnected()

        except KeyboardInterrupt:
            print("\n\n🛑 Остановлено пользователем")
        except Exception as e:
            print(f"\n💥 Критическая ошибка: {e}")
        finally:
            # Корректное завершение
            if self.user_client.is_connected():
                await self.user_client.disconnect()
            print("\n👋 Бот остановлен")


async def main():
    bot = WorkingBot()
    await bot.run()


if __name__ == "__main__":
    # Создаем необходимые папки
    for folder in ['temp']:
        os.makedirs(folder, exist_ok=True)

    # Запускаем бота
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Программа завершена")
    except Exception as e:
        print(f"\n💥 Фатальная ошибка: {e}")