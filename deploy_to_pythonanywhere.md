# 📦 Деплой бота на PythonAnywhere

## 1. Регистрация
1. Перейдите на https://www.pythonanywhere.com/
2. Зарегистрируйтесь (бесплатный аккаунт)
3. Подтвердите email

## 2. Загрузка файлов
1. В Dashboard нажмите "Files"
2. Создайте папку `telegram_bot`
3. Загрузите файлы:
   - `server_bot.py`
   - `requirements_server.txt`
   - `server_session.session` (ваш файл сессии)

## 3. Настройка виртуального окружения
1. Откройте "Consoles" → "Bash"
2. Выполните:
```bash
cd telegram_bot
python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements_server.txt