# test_video_check.py - Тест определения видео
import asyncio
from telethon import TelegramClient


async def test_video_detection():
    print("=" * 60)
    print("🎬 ТЕСТ ОПРЕДЕЛЕНИЯ ВИДЕО В ПОСТАХ")
    print("=" * 60)

    API_ID = 37267988
    API_HASH = "0d6a0ea97840273b408297adf779ff80"

    client = TelegramClient('user_session', API_ID, API_HASH)

    try:
        await client.connect()

        if not await client.is_user_authorized():
            print("❌ Не авторизован")
            return

        print("✅ Подключено")

        # Получаем канал
        channel = await client.get_entity("@tsargradtv")
        print(f"📺 Канал: {channel.title}")

        # Проверяем последние 10 постов
        print("\n🔍 Проверяю последние 10 постов...")

        posts_with_video = []
        posts_with_photo = []
        text_only_posts = []

        async for message in client.iter_messages(channel, limit=10):
            has_video = False
            has_photo = False

            if message.media:
                # Проверяем тип медиа
                media_type = str(type(message.media))

                if 'MessageMediaPhoto' in media_type:
                    has_photo = True
                elif 'MessageMediaDocument' in media_type:
                    # Более детальная проверка для документов
                    doc = message.media.document
                    if hasattr(doc, 'mime_type'):
                        if 'video' in doc.mime_type:
                            has_video = True
                        elif 'image' in doc.mime_type:
                            has_photo = True
                    else:
                        # Проверяем по атрибутам
                        for attr in doc.attributes:
                            if hasattr(attr, 'video'):
                                has_video = True
                                break
                            if hasattr(attr, 'file_name'):
                                filename = attr.file_name.lower()
                                if any(ext in filename for ext in ['.mp4', '.avi', '.mov']):
                                    has_video = True
                                elif any(ext in filename for ext in ['.jpg', '.jpeg', '.png']):
                                    has_photo = True

            # Классифицируем
            if has_video:
                posts_with_video.append(message.id)
                print(f"🎬 Пост {message.id}: ВИДЕО")
            elif has_photo:
                posts_with_photo.append(message.id)
                print(f"🖼 Пост {message.id}: ФОТО")
            elif message.text:
                text_only_posts.append(message.id)
                print(f"📝 Пост {message.id}: ТЕКСТ")
            else:
                print(f"❓ Пост {message.id}: НЕИЗВЕСТНЫЙ ТИП")

        # Результаты
        print(f"\n📊 РЕЗУЛЬТАТЫ:")
        print(f"├ Всего постов: 10")
        print(f"├ С видео: {len(posts_with_video)}")
        print(f"├ С фото: {len(posts_with_photo)}")
        print(f"└ Только текст: {len(text_only_posts)}")

        print(f"\n🎯 Посты с видео (ID): {posts_with_video}")
        print(f"🖼 Посты с фото (ID): {posts_with_photo}")
        print(f"📝 Текстовые посты (ID): {text_only_posts}")

        print(f"\n💡 Рекомендация:")
        print(f"Будет пропущено: {len(posts_with_video)} постов с видео")
        print(f"Будет скопировано: {len(posts_with_photo) + len(text_only_posts)} постов")

    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        if client.is_connected():
            await client.disconnect()


if __name__ == "__main__":
    asyncio.run(test_video_detection())