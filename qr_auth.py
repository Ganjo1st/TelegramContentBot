# qr_auth.py - Авторизация по QR-коду
from telethon import TelegramClient
import asyncio
import os
import sys


async def main():
    print("=" * 60)
    print("📱 АВТОРИЗАЦИЯ ПО QR-КОДУ")
    print("=" * 60)
    print("Это самый надежный способ!")
    print("\nИнструкция:")
    print("1. Откройте Telegram на телефоне")
    print("2. Нажмите 'Настройки' -> 'Устройства' -> 'Подключить устройство'")
    print("3. Отсканируйте QR-код который появится ниже")
    print("=" * 60)

    API_ID = 37267988
    API_HASH = "0d6a0ea97840273b408297adf779ff80"

    client = TelegramClient('user_session', API_ID, API_HASH)

    try:
        # Подключаемся
        await client.connect()

        # Пробуем авторизацию по QR-коду
        qr_login = await client.qr_login()

        print("\n🔗 Ссылка для авторизации:")
        print(qr_login.url)

        print("\n📱 ИЛИ отсканируйте QR-код:")
        qr_login.wait()

        print("\n✅ Авторизация успешна!")

        # Сохраняем сессию
        await client.disconnect()
        print("\n✅ Сессия сохранена!")
        print("\nТеперь запустите бота:")
        print("python main.py")

    except Exception as e:
        print(f"\n❌ Ошибка: {e}")

        # Пробуем обычную авторизацию как запасной вариант
        print("\n🔄 Пробую обычную авторизацию...")
        try:
            if not await client.is_user_authorized():
                phone = input("\nВведите номер телефона (+79161234567): ").strip()
                await client.send_code_request(phone)
                code = input("Введите код: ").strip()
                await client.sign_in(phone, code)
                print("✅ Авторизация успешна!")
        except Exception as e2:
            print(f"❌ Ошибка авторизации: {e2}")

    finally:
        if client.is_connected():
            await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())