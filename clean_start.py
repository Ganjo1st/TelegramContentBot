# clean_start.py - Чистый старт
import os
import shutil
import json

print("="*60)
print("🔄 ЧИСТЫЙ СТАРТ БОТА")
print("="*60)

# Удаляем старые файлы
files_to_remove = [
    'processed_ids.json',
    'optimized_ids.json',
    'processed.txt',
    'user_session.session'
]

for file in files_to_remove:
    if os.path.exists(file):
        os.remove(file)
        print(f"🗑 Удален: {file}")

# Удаляем папки
folders_to_remove = ['temp', 'temp_downloads', 'backup', 'logs']
for folder in folders_to_remove:
    if os.path.exists(folder):
        shutil.rmtree(folder)
        print(f"🗑 Удалена папка: {folder}")

print("\n✅ Все очищено!")
print("\nТеперь запустите бота заново:")
print("python optimized_bot.py")
print("="*60)