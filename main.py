# main.py - Исправленная версия
import asyncio
import logging
import os
import re
import json
import hashlib
import sys
from datetime import datetime
from telethon import TelegramClient, events
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument
from telegram import Bot
from telegram.error import TelegramError

import config

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.LOG_FILE, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class TelegramContentBot:
    def __init__(self):
        # User-клиент для чтения канала
        self.user_client = TelegramClient(
            'user_session',
            config.API_ID,
            config.API_HASH
        )

        # Бот для отправки
        self.bot = Bot(token=config.BOT_TOKEN)

        self.processed_ids = self.load_processed_ids()
        logger.info(f"Загружено {len(self.processed_ids)} обработанных ID")

    def load_processed_ids(self):
        """Загружает обработанные ID"""
        try:
            if os.path.exists(config.PROCESSED_IDS_FILE):
                with open(config.PROCESSED_IDS_FILE, 'r', encoding='utf-8') as f:
                    ids = set(line.strip() for line in f if line.strip())
                    logger.info(f"Загружено {len(ids)} ID")
                    return ids
            return set()
        except Exception as e:
            logger.error(f"Ошибка загрузки ID: {e}")
            return set()

    def save_processed_id(self, post_id):
        """Сохраняет ID"""
        try:
            with open(config.PROCESSED_IDS_FILE, 'a', encoding='utf-8') as f:
                f.write(f"{post_id}\n")
            self.processed_ids.add(post_id)
        except Exception as e:
            logger.error(f"Ошибка сохранения ID: {e}")

    def clean_text(self, text):
        """
        Очищает текст:
        1. Удаляет все абзацы с ссылками
        2. Удаляет отдельные ссылки
        3. Добавляет ссылку на источник в конце
        """
        if not text:
            return config.SOURCE_LINK

        original_lines = text.split('\n')
        cleaned_lines = []

        for line in original_lines:
            # Проверяем, содержит ли строка ссылку
            has_url = re.search(r'https?://|t\.me/|@\w+|bit\.ly|t\.co|goo\.gl|tinyurl', line, re.IGNORECASE)

            # Если строка НЕ содержит ссылку, добавляем ее
            if not has_url:
                # Очищаем от маркеров канала
                if not re.search(r'🤴\s*\[\*\*Царьград\.ТВ|Царьград\.ТВ\s*—', line):
                    cleaned_lines.append(line)

        # Объединяем обратно
        cleaned_text = '\n'.join(cleaned_lines)

        # Удаляем одиночные ссылки, которые могли остаться
        cleaned_text = re.sub(r'https?://\S+', '', cleaned_text)
        cleaned_text = re.sub(r't\.me/\S+', '', cleaned_text)
        cleaned_text = re.sub(r'@\w+', '', cleaned_text)

        # Удаляем рекламные фразы
        ad_patterns = [
            r'Подписывайтесь.*',
            r'Подпишись.*',
            r'Читайте также.*',
            r'Смотрите также.*',
            r'Источник:.*',
            r'Перейти:.*',
            r'Ссылка:.*',
            r'Рекомендуем:.*',
            r'Также читайте.*',
            r'Больше новостей.*',
            r'Читать далее.*',
            r'Смотреть далее.*',
            r'#\w+\s*$'
        ]

        for pattern in ad_patterns:
            cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.IGNORECASE)

        # Очищаем форматирование
        cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text)
        cleaned_text = re.sub(r'[ \t]{2,}', ' ', cleaned_text)
        cleaned_text = cleaned_text.strip()

        # Если текст остался - добавляем ссылку
        if cleaned_text:
            cleaned_text = f"{cleaned_text}\n\n{config.SOURCE_LINK}"
        else:
            cleaned_text = config.SOURCE_LINK

        return cleaned_text

    async def download_media(self, message):
        """Скачивает медиа файл"""
        try:
            if not message.media:
                return None

            # Создаем папку для временных файлов
            os.makedirs("temp", exist_ok=True)

            # Генерируем имя файла
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            msg_id = message.id

            # Определяем расширение файла
            if isinstance(message.media, MessageMediaPhoto):
                filename = f"temp/photo_{msg_id}_{timestamp}.jpg"
            elif isinstance(message.media, MessageMediaDocument):
                doc = message.media.document
                original_filename = None
                for attr in doc.attributes:
                    if hasattr(attr, 'file_name'):
                        original_filename = attr.file_name
                        break

                if original_filename:
                    ext = os.path.splitext(original_filename)[1]
                    filename = f"temp/file_{msg_id}_{timestamp}{ext}"
                else:
                    filename = f"temp/file_{msg_id}_{timestamp}.bin"
            else:
                return None

            # Скачиваем файл
            await message.download_media(file=filename)
            logger.info(f"Скачан файл: {filename}")

            return filename

        except Exception as e:
            logger.error(f"Ошибка скачивания медиа: {e}")
            return None

    async def send_to_channel(self, text, media_path=None):
        """Отправляет пост в целевой канал"""
        try:
            if media_path and os.path.exists(media_path):
                # Определяем тип файла
                ext = os.path.splitext(media_path)[1].lower()

                with open(media_path, 'rb') as file:
                    if ext in ['.mp4', '.avi', '.mov', '.mkv', '.webm']:
                        await self.bot.send_video(
                            chat_id=config.TARGET_CHANNEL,
                            video=file,
                            caption=text,
                            parse_mode='HTML',
                            supports_streaming=True
                        )
                        logger.info("Отправлено видео")

                    elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
                        await self.bot.send_photo(
                            chat_id=config.TARGET_CHANNEL,
                            photo=file,
                            caption=text,
                            parse_mode='HTML'
                        )
                        logger.info("Отправлено фото")

                    else:
                        await self.bot.send_document(
                            chat_id=config.TARGET_CHANNEL,
                            document=file,
                            caption=text,
                            parse_mode='HTML'
                        )
                        logger.info("Отправлен документ")
            else:
                # Только текст
                await self.bot.send_message(
                    chat_id=config.TARGET_CHANNEL,
                    text=text,
                    parse_mode='HTML'
                )
                logger.info("Отправлен текст")

            return True

        except TelegramError as e:
            logger.error(f"Ошибка Telegram при отправке: {e}")
            return False
        except Exception as e:
            logger.error(f"Общая ошибка при отправке: {e}")
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
                logger.debug(f"Пропускаем уже обработанный ID: {msg_id}")
                return False

            logger.info(f"Обработка сообщения ID: {msg_id}")

            # Получаем текст
            text = message.text or message.message or ""

            # Очищаем текст
            cleaned_text = self.clean_text(text)

            # Скачиваем медиа
            media_path = None
            if message.media:
                media_path = await self.download_media(message)

            # Отправляем в канал
            success = await self.send_to_channel(cleaned_text, media_path)

            if success:
                # Сохраняем ID
                self.save_processed_id(msg_id)
                logger.info(f"Успешно обработано: {msg_id}")
                return True
            else:
                logger.error(f"Ошибка отправки: {msg_id}")
                return False

        except Exception as e:
            logger.error(f"Критическая ошибка обработки: {e}")
            return False

    async def check_recent_messages(self):
        """Проверяет последние сообщения в канале"""
        try:
            logger.info("Проверка последних сообщений...")

            # Получаем сущность канала
            entity = await self.user_client.get_entity(config.SOURCE_CHANNEL)
            logger.info(f"Канал: {entity.title}")

            # Получаем последние сообщения
            messages = []
            async for message in self.user_client.iter_messages(entity, limit=10):
                messages.append(message)

            logger.info(f"Найдено {len(messages)} сообщений")

            # Обрабатываем в правильном порядке
            processed_count = 0
            for message in reversed(messages):
                if await self.process_message(message):
                    processed_count += 1
                    await asyncio.sleep(1)

            logger.info(f"Обработано {processed_count} новых сообщений")

        except Exception as e:
            logger.error(f"Ошибка при проверке сообщений: {e}")

    async def setup_session(self):
        """Настраивает сессию пользователя"""
        try:
            print("\n" + "=" * 50)
            print("📱 АВТОРИЗАЦИЯ TELEGRAM")
            print("=" * 50)
            print("Выберите способ авторизации:")
            print("1. По номеру телефона (придет код в Telegram)")
            print("2. По номеру телефона и паролю (если включена 2FA)")
            print("3. Использовать уже сохраненную сессию")
            print("=" * 50 + "\n")

            # Подключаемся
            await self.user_client.connect()

            # Если уже авторизован
            if await self.user_client.is_user_authorized():
                print("✅ Используем сохраненную сессию")
                return True

            # Выбираем способ
            choice = input("Выберите способ (1/2/3): ").strip()

            if choice == "3":
                if os.path.exists('user_session.session'):
                    print("✅ Сессия найдена, пробуем подключиться...")
                    return await self.user_client.is_user_authorized()
                else:
                    print("❌ Файл сессии не найден")
                    return False

            # Запрашиваем номер
            phone = input("\nВведите номер телефона (например +79161234567): ").strip()

            if choice == "1":
                # Способ 1: Только код
                await self.user_client.send_code_request(phone)
                code = input("Введите код из Telegram: ").strip()
                await self.user_client.sign_in(phone, code)

            elif choice == "2":
                # Способ 2: Код + пароль
                await self.user_client.send_code_request(phone)
                code = input("Введите код из Telegram: ").strip()
                password = input("Введите пароль 2FA: ").strip()
                await self.user_client.sign_in(phone=phone, code=code, password=password)

            print("✅ Авторизация успешна!")
            return True

        except Exception as e:
            print(f"\n❌ Ошибка авторизации: {e}")

            # Если ошибка связана с сессией
            if "session" in str(e):
                print("\n🔄 Пробуем создать новую сессию...")
                try:
                    os.remove('user_session.session')
                    print("🗑 Удален старый файл сессии")
                except:
                    pass

                # Пробуем еще раз
                return await self.setup_session()

            return False

    async def run(self):
        """Запускает бота"""
        print("=" * 50)
        print("🤖 TELEGRAM CONTENT BOT")
        print("=" * 50)
        print(f"📺 Источник: {config.SOURCE_CHANNEL}")
        print(f"📤 Приемник: {config.TARGET_CHANNEL}")
        print("=" * 50)

        try:
            # Настраиваем user-сессию
            if not await self.setup_session():
                print("❌ Не удалось настроить сессию")
                return

            # Проверяем бота
            bot_info = await self.bot.get_me()
            print(f"✅ Бот: @{bot_info.username}")

            # Получаем информацию о каналах
            source_entity = await self.user_client.get_entity(config.SOURCE_CHANNEL)
            print(f"✅ Канал-источник: {source_entity.title}")

            # Первоначальная проверка
            print("\n🔄 Проверка последних постов...")
            await self.check_recent_messages()

            # Настраиваем обработчик новых сообщений
            @self.user_client.on(events.NewMessage(chats=source_entity))
            async def new_message_handler(event):
                """Обработчик новых сообщений"""
                print(f"\n📨 НОВОЕ СООБЩЕНИЕ (ID: {event.message.id})")
                await self.process_message(event.message)

            print("\n" + "=" * 50)
            print("✅ БОТ ЗАПУЩЕН")
            print("=" * 50)
            print("📡 Ожидание новых сообщений...")
            print("🛑 Ctrl+C для остановки")
            print("=" * 50 + "\n")

            # Запускаем ожидание
            await self.user_client.run_until_disconnected()

        except KeyboardInterrupt:
            print("\n\n🛑 Остановлено пользователем")
        except Exception as e:
            print(f"\n💥 Ошибка: {e}")
        finally:
            # Корректное завершение
            if self.user_client.is_connected():
                await self.user_client.disconnect()
            print("\n👋 Бот остановлен")


async def main():
    bot = TelegramContentBot()
    await bot.run()


if __name__ == "__main__":
    # Создаем необходимые папки
    for folder in ['data', 'logs', 'temp']:
        os.makedirs(folder, exist_ok=True)

    # Запускаем бота
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Программа завершена")
    except Exception as e:
        print(f"\n💥 Фатальная ошибка: {e}")