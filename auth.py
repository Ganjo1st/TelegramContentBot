# auth.py - Отдельный скрипт для авторизации
from telethon import TelegramClient
import asyncio
import os


async def main():
    print("=" * 60)
    print("🔐 НАСТРОЙКА АВТОРИЗАЦИИ TELEGRAM")
    print("=" * 60)

    # Данные из config.py
    API_ID = 37267988
    API_HASH = "0d6a0ea97840273b408297adf779ff80"

    client = TelegramClient('user_session', API_ID, API_HASH)

    try:
        await client.connect()

        if not await client.is_user_authorized():
            print("\n📱 Введите номер телефона:")
            print("Пример: +79513722340")
            phone = input("Номер: ").strip()

            print("\n📨 Запрашиваю код...")
            sent_code = await client.send_code_request(phone)

            print(f"\n📲 Код отправлен через: {sent_code.type}")
            print("Если код не пришел, проверьте:")
            print("1. Правильность номера")
            print("2. Приложение Telegram на телефоне")
            print("3. Попробуйте позже")

            code = input("\nВведите код: ").strip()

            try:
                # Пробуем войти с кодом
                await client.sign_in(phone, code)
                print("✅ Авторизация успешна!")

            except Exception as e:
                if "password" in str(e):
                    print("\n🔐 Требуется пароль 2FA")
                    password = input("Введите пароль: ").strip()
                    await client.sign_in(password=password)
                    print("✅ Авторизация с паролем успешна!")
                else:
                    raise e

        # Сохраняем сессию
        await client.disconnect()
        print("\n✅ Сессия сохранена в файл: user_session.session")
        print("\nТеперь можно запустить бота:")
        print("python main.py")

    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        print("\nПопробуйте:")
        print("1. Проверить номер телефона")
        print("2. Убедиться, что Telegram установлен на телефоне")
        print("3. Попробовать другой способ авторизации")

    finally:
        if client.is_connected():
            await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())