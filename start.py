# start.py - Простой запуск бота
import subprocess
import sys
import os


def install_packages():
    """Устанавливает необходимые пакеты"""
    packages = [
        'telethon',
        'python-telegram-bot',
        'httpx',
        'aiohttp'
    ]

    print("📦 Установка зависимостей...")
    for package in packages:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✅ {package} установлен")
        except:
            print(f"⚠ Ошибка установки {package}")


def check_folders():
    """Проверяет наличие папок"""
    folders = ['data', 'logs', 'temp']
    for folder in folders:
        if not os.path.exists(folder):
            os.makedirs(folder)
            print(f"✅ Создана папка: {folder}")


if __name__ == "__main__":
    print("=" * 50)
    print("🚀 ЗАПУСК ТЕЛЕГРАМ БОТА")
    print("=" * 50)

    check_folders()

    # Спрашиваем, установить ли зависимости
    answer = input("\nУстановить зависимости? (y/n): ").lower()
    if answer == 'y':
        install_packages()

    print("\n✅ Все готово!")
    print("Запускаем бота...")
    print("=" * 50 + "\n")

    # Запускаем main.py
    os.system(f'{sys.executable} main.py')