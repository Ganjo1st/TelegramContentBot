# qr_login.py - Авторизация по QR-коду
from telethon import TelegramClient
import asyncio
import qrcode
from io import BytesIO


async def main():
    print("=" * 60)
    print("📱 АВТОРИЗАЦИЯ ПО QR-КОДУ")
    print("=" * 60)

    API_ID = 37267988
    API_HASH = "0d6a0ea97840273b408297adf779ff80"

    client = TelegramClient('user_session', API_ID, API_HASH)

    try:
        await client.connect()

        if not await client.is_user_authorized():
            print("\n🔗 Получаю ссылку для авторизации...")

            # Получаем QR-код
            qr_login = await client.qr_login()

            print(f"\n📱 Отсканируйте QR-код в Telegram:")
            print("1. Откройте Telegram на телефоне")
            print("2. Нажмите 'Настройки' -> 'Устройства' -> 'Подключить устройство'")
            print("3. Отсканируйте QR-код")

            # Показываем QR-код в консоли
            qr = qrcode.QRCode()
            qr.add_data(qr_login.url)

            print("\n" + "=" * 60)
            print("QR-код для сканирования:")
            qr.print_ascii(invert=True)
            print("=" * 60)

            # Ждем сканирования
            await qr_login.wait()

            print("\n✅ Авторизация успешна!")

        await client.disconnect()
        print("\n✅ Сессия сохранена!")
        print("\nТеперь запустите бота:")
        print("python working_bot.py")

    except Exception as e:
        print(f"\n❌ Ошибка: {e}")


if __name__ == "__main__":
    asyncio.run(main())