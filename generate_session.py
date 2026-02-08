# generate_session.py - Запустите ОДИН РАЗ на своем компьютере
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession


async def main():
    print("=" * 60)
    print("🔐 ГЕНЕРАЦИЯ СЕССИИ ДЛЯ RAILWAY")
    print("=" * 60)

    API_ID = 37267988
    API_HASH = "0d6a0ea97840273b408297adf779ff80"
    PHONE = "+79513722340"

    client = TelegramClient(StringSession(), API_ID, API_HASH)

    await client.connect()
    print("📡 Подключение к Telegram...")

    if not await client.is_user_authorized():
        print("📱 Отправка кода на телефон...")
        await client.send_code_request(PHONE)

        code = input("📝 Введите код из Telegram (5 цифр): ")

        try:
            await client.sign_in(PHONE, code)
            print("✅ Авторизация успешна!")
        except Exception as e:
            print(f"❌ Ошибка авторизации: {e}")
            return
    else:
        print("✅ Уже авторизован")

    session_string = client.session.save()

    print("\n" + "=" * 60)
    print("🎉 СЕССИЯ СОЗДАНА!")
    print("=" * 60)
    print("\n📋 СКОПИРУЙТЕ ВСЮ ЭТУ СТРОКУ (она длинная):")
    print("-" * 60)
    print(session_string)
    print("-" * 60)

    with open('telegram_session.txt', 'w', encoding='utf-8') as f:
        f.write(session_string)

    print(f"\n💾 Также сохранено в файл: telegram_session.txt")
    print("🔑 Длина сессии:", len(session_string), "символов")

    try:
        me = await client.get_me()
        print(f"\n👤 Авторизован как: {me.first_name} (@{me.username})")
    except:
        pass

    await client.disconnect()
    print("\n✅ Готово! Скопируйте строку выше в Railway.")


if __name__ == "__main__":
    asyncio.run(main())