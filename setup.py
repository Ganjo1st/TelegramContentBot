# setup.py - для правильной установки зависимостей
from setuptools import setup, find_packages

setup(
    name="telegram-content-bot",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "telethon==1.34.0",
        "python-telegram-bot==20.3",
        "aiohttp==3.9.3",
        "aiofiles==23.2.1",
        "Pillow==9.5.0",
        "python-dotenv==1.0.0"
    ],
    python_requires=">=3.8",
)