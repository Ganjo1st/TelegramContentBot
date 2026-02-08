# server_bot.py - Бот для работы на сервере 24/7
import asyncio
import os
import re
import json
import time
import sys
import logging
from datetime import datetime, timedelta
from telethon import TelegramClient, events
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument
from telegram import Bot
from telegram.request import HTTPXRequest

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot_server.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Конфигурация (лучше вынести в отдельный файл или переменные окружения)
API_ID = 37267988
API_HASH = "0d6a0ea97840273b408297adf779ff80"
BOT_TOKEN = "8459279128:AAGsWSNhVNQH57NFignIpEDQ-PcipAxfD9Y"
SOURCE_CHANNEL = "@tsargradtv"
TARGET_CHANNEL = "@Chanal_in_1"


class ServerBot:
    def __init__(self):
        self.is_running = True
        self.restart_count = 0
        self.max_restarts = 10

        # Клиенты будут инициализированы в connect()
        self.user_client = None
        self.bot = None

        # Настройки
        self.skip_videos = True
        self.process_photos = True
        self.process_text = True

        # Данные
        self.processed_ids = self.load_data()
        self.stats = self.load_stats()

        logger.info(f"🚀 Серверный бот инициализирован")
        logger.info(f"📊 Загружено {len(self.processed_ids)} обработанных ID")

    def load_data(self):
        """Загружает данные из файла"""
        try:
            if os.path.exists('server_data.json'):
                with open('server_data.json', 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return set(data.get('processed_ids', []))
        except Exception as e:
            logger.error(f"Ошибка загрузки данных: {e}")
        return set()

    def load_stats(self):
        """Загружает статистику"""
        default_stats = {
            'total_processed': 0,
            'successful': 0,
            'skipped_video': 0,
            'skipped_other': 0,
            'errors': 0,
            'restarts': 0,
            'uptime': 0,
            'start_time': datetime.now().isoformat(),
            'last_post_time': None
        }

        try:
            if os.path.exists('server_stats.json'):
                with open('server_stats.json', 'r', encoding='utf-8') as f:
                    stats = json.load(f)
                    # Обновляем только некоторые поля
                    stats['start_time'] = datetime.now().isoformat()
                    stats['restarts'] = stats.get('restarts', 0) + 1
                    return stats
        except:
            pass

        return default_stats

    def save_data(self):
        """Сохраняет данные"""
        try:
            data = {
                'processed_ids': list(self.processed_ids),
                'last_save': datetime.now().isoformat(),
                'total_ids': len(self.processed_ids)
            }
            with open('server_data.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            # Также сохраняем резервную копию
            backup_file = f"backup/server_data_{int(time.time())}.json"
            os.makedirs('backup', exist_ok=True)
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error(f"Ошибка сохранения данных: {e}")

    def save_stats(self):
        """Сохраняет статистику"""
        try:
            # Обновляем аптайм
            start_time = datetime.fromisoformat(self.stats['start_time'])
            uptime = datetime.now() - start_time
            self.stats['uptime'] = int(uptime.total_seconds())

            with open('server_stats.json', 'w', encoding='utf-8') as f:
                json.dump(self.stats, f, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error(f"Ошибка сохранения статистики: {e}")

    async def connect_clients(self):
        """Подключает клиентов"""
        max_retries = 5
        retry_delay = 10

        for attempt in range(max_retries):
            try:
                logger.info(f"Попытка подключения {attempt + 1}/{max_retries}")

                # Подключаем user-клиент
                self.user_client = TelegramClient('server_session', API_ID, API_HASH)
                await self.user_client.connect()

                if not await self.user_client.is_user_authorized():
                    logger.error("User-клиент не авторизован")
                    # На сервере нельзя вводить код, нужна сохраненная сессия
                    if not os.path.exists('server_session.session'):
                        logger.critical("Файл сессии не найден!")
                        return False
                    logger.warning("Используем существующую сессию")

                # Подключаем бота
                request = HTTPXRequest(
                    connect_timeout=30,
                    read_timeout=30,
                    write_timeout=30,
                    pool_timeout=30
                )
                self.bot = Bot(token=BOT_TOKEN, request=request)

                # Проверяем подключение
                bot_info = await self.bot.get_me()
                logger.info(f"✅ Бот подключен: @{bot_info.username}")

                # Получаем информацию о канале
                channel = await self.user_client.get_entity(SOURCE_CHANNEL)
                logger.info(f"📺 Канал подключен: {channel.title}")

                return True

            except Exception as e:
                logger.error(f"Ошибка подключения (попытка {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    logger.info(f"Жду {retry_delay} секунд перед повторной попыткой...")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Экспоненциальная задержка

        return False

    def clean_text(self, text):
        """Очищает текст"""
        if not text:
            return '<a href="https://t.me/tsargradtv">ЦарьградТВ</a>'

        # Удаляем ссылки
        text = re.sub(r'https?://\S+', '', text)
        text = re.sub(r't\.me/\S+', '', text)
        text = re.sub(r'@\w+', '', text)

        # Удаляем рекламу
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
            r'Читайте также.*',
            r'Смотрите также.*',
            r'Источник:.*',
            r'\d{1,2}:\d{2}.*',
        ]

        for pattern in ad_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)

        # Фильтруем строки
        lines = text.split('\n')
        clean_lines = []

        for line in lines:
            line = line.strip()
            if not line or len(line) < 10:  # Минимум 10 символов
                continue

            ad_words = ['подпис', 'читайте', 'смотрите', 'источник',
                        'перейти', 'ссылка', 'рекомендуем', 'больше',
                        'далее', 'подробнее', 'официальный', 'наш',
                        'присоединяйтесь', 'делитесь', 'редакция', 'реклама']

            line_lower = line.lower()
            if not any(word in line_lower for word in ad_words):
                clean_lines.append(line)

        # Объединяем
        result = '\n'.join(clean_lines)
        result = re.sub(r'\s+', ' ', result)
        result = re.sub(r'\n\s*\n+', '\n\n', result)
        result = result.strip()

        # Добавляем ссылку
        if result:
            return f"{result}\n\n<a href=\"https://t.me/tsargradtv\">ЦарьградТВ</a>"
        return '<a href="https://t.me/tsargradtv">ЦарьградТВ</a>'

    def has_video(self, message):
        """Проверяет видео"""
        if not message.media:
            return False

        try:
            if isinstance(message.media, MessageMediaDocument):
                doc = message.media.document
                if hasattr(doc, 'mime_type') and 'video' in doc.mime_type:
                    return True

                # Проверяем по атрибутам
                if hasattr(doc, 'attributes'):
                    for attr in doc.attributes:
                        if hasattr(attr, 'video'):
                            return True
                        if hasattr(attr, 'file_name'):
                            filename = attr.file_name.lower()
                            if any(ext in filename for ext in ['.mp4', '.avi', '.mov', '.mkv']):
                                return True
        except:
            pass

        return False

    async def process_message(self, message):
        """Обрабатывает сообщение"""
        try:
            msg_id = str(message.id)

            if msg_id in self.processed_ids:
                return False

            self.stats['total_processed'] += 1
            logger.info(f"Обработка поста {msg_id}")

            # Проверяем видео
            if self.skip_videos and self.has_video(message):
                logger.info(f"🚫 Пропущено видео: {msg_id}")
                self.processed_ids.add(msg_id)
                self.stats['skipped_video'] += 1
                return False

            # Текст
            text = message.text or message.message or ""
            cleaned = self.clean_text(text)

            # Отправляем (только текст для надежности)
            try:
                await self.bot.send_message(
                    chat_id=TARGET_CHANNEL,
                    text=cleaned,
                    parse_mode='HTML'
                )

                self.processed_ids.add(msg_id)
                self.stats['successful'] += 1
                self.stats['last_post_time'] = datetime.now().isoformat()

                logger.info(f"✅ Отправлено: {msg_id}")

                # Сохраняем каждые 5 постов
                if self.stats['successful'] % 5 == 0:
                    self.save_data()
                    self.save_stats()

                return True

            except Exception as e:
                logger.error(f"❌ Ошибка отправки {msg_id}: {e}")
                self.stats['errors'] += 1
                return False

        except Exception as e:
            logger.error(f"💥 Ошибка обработки: {e}")
            self.stats['errors'] += 1
            return False

        finally:
            # Пауза
            await asyncio.sleep(3)

    async def check_recent_posts(self):
        """Проверяет последние посты"""
        try:
            logger.info("Проверка последних постов...")

            channel = await self.user_client.get_entity(SOURCE_CHANNEL)

            messages = []
            async for msg in self.user_client.iter_messages(channel, limit=20):
                messages.append(msg)

            logger.info(f"Найдено {len(messages)} сообщений")

            # Обрабатываем
            for msg in reversed(messages):
                await self.process_message(msg)
                if not self.is_running:
                    break

            # Сохраняем
            self.save_data()
            self.save_stats()

        except Exception as e:
            logger.error(f"Ошибка проверки постов: {e}")

    async def health_check(self):
        """Проверка здоровья бота"""
        while self.is_running:
            try:
                # Проверяем подключение
                if not self.user_client.is_connected():
                    logger.warning("Соединение разорвано, переподключаюсь...")
                    await self.user_client.connect()

                # Отправляем статус каждые 30 минут
                current_time = datetime.now()
                if current_time.minute % 30 == 0 and current_time.second < 10:
                    uptime = datetime.now() - datetime.fromisoformat(self.stats['start_time'])
                    hours = uptime.seconds // 3600
                    minutes = (uptime.seconds % 3600) // 60

                    status_msg = (
                        f"🤖 Бот работает\n"
                        f"⏰ Аптайм: {hours}ч {minutes}м\n"
                        f"📊 Обработано: {self.stats['successful']}\n"
                        f"🚫 Пропущено видео: {self.stats['skipped_video']}\n"
                        f"⚡ Рестартов: {self.stats['restarts']}"
                    )

                    try:
                        await self.bot.send_message(
                            chat_id=TARGET_CHANNEL,
                            text=status_msg
                        )
                        logger.info("Отправлен статус бота")
                    except:
                        pass

                await asyncio.sleep(60)  # Проверка каждую минуту

            except Exception as e:
                logger.error(f"Ошибка health check: {e}")
                await asyncio.sleep(60)

    async def run(self):
        """Основной цикл работы"""
        logger.info("=" * 70)
        logger.info("🚀 ЗАПУСК СЕРВЕРНОГО БОТА")
        logger.info("=" * 70)

        while self.is_running and self.restart_count < self.max_restarts:
            try:
                # Подключаемся
                logger.info("Подключение к Telegram...")
                if not await self.connect_clients():
                    logger.error("Не удалось подключиться")
                    break

                # Первоначальная проверка
                await self.check_recent_posts()

                # Запускаем health check в фоне
                health_task = asyncio.create_task(self.health_check())

                # Настраиваем обработчик новых сообщений
                channel = await self.user_client.get_entity(SOURCE_CHANNEL)

                @self.user_client.on(events.NewMessage(chats=channel))
                async def handler(event):
                    logger.info(f"📨 Новое сообщение: {event.message.id}")
                    await self.process_message(event.message)

                logger.info("✅ Бот запущен и готов к работе")
                logger.info(f"📡 Мониторинг: {SOURCE_CHANNEL}")
                logger.info(f"📤 Отправка в: {TARGET_CHANNEL}")
                logger.info("🔄 Health check запущен")

                # Ждем пока бот работает
                await self.user_client.run_until_disconnected()

                # Если дошли сюда, соединение разорвано
                logger.warning("Соединение разорвано, переподключаюсь...")

                # Отменяем health check
                health_task.cancel()
                try:
                    await health_task
                except asyncio.CancelledError:
                    pass

                # Увеличиваем счетчик рестартов
                self.restart_count += 1
                self.stats['restarts'] += 1

                if self.restart_count < self.max_restarts:
                    logger.info(f"Рестарт {self.restart_count}/{self.max_restarts}")
                    await asyncio.sleep(10)  # Пауза перед рестартом
                else:
                    logger.error(f"Достигнут максимум рестартов: {self.max_restarts}")
                    break

            except KeyboardInterrupt:
                logger.info("Получен сигнал остановки")
                break

            except Exception as e:
                logger.error(f"Критическая ошибка в основном цикле: {e}")
                self.restart_count += 1
                self.stats['restarts'] += 1

                if self.restart_count < self.max_restarts:
                    logger.info(f"Рестарт после ошибки {self.restart_count}/{self.max_restarts}")
                    await asyncio.sleep(30)
                else:
                    logger.error(f"Достигнут максимум рестартов после ошибок")
                    break

        # Завершение работы
        self.is_running = False

        # Сохраняем данные
        self.save_data()
        self.save_stats()

        # Отключаемся
        try:
            if self.user_client and self.user_client.is_connected():
                await self.user_client.disconnect()
        except:
            pass

        logger.info("👋 Бот остановлен")

        # Показываем финальную статистику
        uptime = datetime.now() - datetime.fromisoformat(self.stats['start_time'])
        logger.info(f"📊 ФИНАЛЬНАЯ СТАТИСТИКА:")
        logger.info(f"  Аптайм: {uptime}")
        logger.info(f"  Обработано: {self.stats['successful']}")
        logger.info(f"  Пропущено видео: {self.stats['skipped_video']}")
        logger.info(f"  Ошибок: {self.stats['errors']}")
        logger.info(f"  Рестартов: {self.stats['restarts']}")


async def main():
    # Создаем необходимые папки
    for folder in ['backup', 'logs']:
        os.makedirs(folder, exist_ok=True)

    bot = ServerBot()
    await bot.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Программа завершена")
    except Exception as e:
        print(f"\n💥 Фатальная ошибка: {e}")
        # Пытаемся сохранить что можно
        try:
            import json

            with open('crash_report.json', 'w') as f:
                json.dump({
                    'error': str(e),
                    'time': datetime.now().isoformat()
                }, f)
        except:
            pass