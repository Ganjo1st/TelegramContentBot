async def main():
    print("🚀 Запуск основного цикла бота...")
    print(f"⏰ Время старта: {datetime.now().strftime('%H:%M:%S')}")
    
    # Инициализация клиента ВНУТРИ функции main
    if SESSION_STRING:
        print("📱 Используется строковая сессия")
        client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
    else:
        print("📱 Будет создана новая сессия")
        client = TelegramClient('bot_session', API_ID, API_HASH)
    
    # Запускаем клиент
    await client.start()
    print(f"✅ Telethon клиент запущен. ID: {(await client.get_me()).id}")
    
    # Регистрируем обработчики
    client.add_event_handler(new_message_handler, events.NewMessage(chats=SOURCE_CHANNEL))
    
    print(f"👂 Ожидание новых сообщений из {SOURCE_CHANNEL}...")
    print("=" * 70)
    
    # Бесконечный цикл (healthcheck обрабатывается отдельным Flask сервером)
    await client.run_until_disconnected()
