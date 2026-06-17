import os
import sys
import json
import telebot
from telebot import types
import schedule
import time
import threading
from datetime import datetime, timedelta
import re

# ========== ДИАГНОСТИКА ПРИ ЗАПУСКЕ ==========
print("=" * 60)
print("🚀 ЗАПУСК БОТА (main.py)")

# Проверяем переменные окружения
TOKEN = os.getenv('BOT_TOKEN')
if TOKEN:
    print(f"✅ Токен найден! Длина: {len(TOKEN)} символов")
else:
    print("❌ ТОКЕН НЕ НАЙДЕН! Проверьте переменную BOT_TOKEN на Render")
    sys.exit(1)

print("=" * 60)
sys.stdout.flush()

# ========== ИНИЦИАЛИЗАЦИЯ БОТА ==========
bot = telebot.TeleBot(TOKEN)

# Путь к файлу с данными
DATA_FILE = 'data/users.json'

# ========== ФУНКЦИИ РАБОТЫ С ДАННЫМИ ==========
def load_users():
    """Загружает данные пользователей из JSON-файла"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    return json.loads(content)
                return {}
        except:
            return {}
    return {}

def save_users(users):
    """Сохраняет данные пользователей в JSON-файл"""
    os.makedirs('data', exist_ok=True)
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

def get_user_data(user_id):
    """Получает данные конкретного пользователя"""
    users = load_users()
    user_id_str = str(user_id)
    if user_id_str not in users:
        users[user_id_str] = {'tasks': [], 'notes': [], 'name': ''}
        save_users(users)
    return users[user_id_str]

def save_user_data(user_id, data):
    """Сохраняет данные конкретного пользователя"""
    users = load_users()
    user_id_str = str(user_id)
    users[user_id_str] = data
    save_users(users)

# ========== КОМАНДА /start ==========
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    user_data = get_user_data(user_id)
    
    welcome_text = f"""
👋 Привет, {message.from_user.first_name}!

Я TaskyBot — твой помощник для организации задач и заметок.

📋 Что я умею:
/tasks — список задач
/addtask — добавить задачу
/donetask — отметить задачу как выполненную
/deletetask — удалить задачу

📝 Заметки:
/notes — список заметок
/addnote — добавить заметку
/deletenote — удалить заметку

🌐 Веб-версия: https://taskybot-zzq3.onrender.com
    """
    bot.reply_to(message, welcome_text)

# ========== КОМАНДА /tasks ==========
@bot.message_handler(commands=['tasks'])
def show_tasks(message):
    user_id = message.from_user.id
    user_data = get_user_data(user_id)
    tasks = user_data.get('tasks', [])
    
    if not tasks:
        bot.reply_to(message, "📭 У тебя пока нет задач!")
        return
    
    text = "📋 *Твои задачи:*\n\n"
    for i, task in enumerate(tasks, 1):
        status = "✅" if task.get('done', False) else "⬜"
        text += f"{i}. {status} {task.get('text', '')}\n"
    
    bot.reply_to(message, text, parse_mode='Markdown')

# ========== КОМАНДА /addtask ==========
@bot.message_handler(commands=['addtask'])
def add_task(message):
    try:
        # Извлекаем текст задачи после команды
        task_text = message.text.replace('/addtask', '').strip()
        if not task_text:
            bot.reply_to(message, "⚠️ Напиши задачу после команды.\nПример: /addtask Купить молоко")
            return
        
        user_id = message.from_user.id
        user_data = get_user_data(user_id)
        
        if 'tasks' not in user_data:
            user_data['tasks'] = []
        
        user_data['tasks'].append({
            'text': task_text,
            'done': False,
            'created': datetime.now().isoformat()
        })
        
        save_user_data(user_id, user_data)
        bot.reply_to(message, f"✅ Задача добавлена:\n{task_text}")
        
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")

# ========== КОМАНДА /donetask ==========
@bot.message_handler(commands=['donetask'])
def done_task(message):
    try:
        parts = message.text.split(maxsplit=1)
        if len(parts) < 2:
            bot.reply_to(message, "⚠️ Укажи номер задачи.\nПример: /donetask 1")
            return
        
        task_num = int(parts[1]) - 1
        user_id = message.from_user.id
        user_data = get_user_data(user_id)
        tasks = user_data.get('tasks', [])
        
        if task_num < 0 or task_num >= len(tasks):
            bot.reply_to(message, "❌ Задача с таким номером не найдена!")
            return
        
        tasks[task_num]['done'] = True
        save_user_data(user_id, user_data)
        bot.reply_to(message, f"✅ Задача выполнена:\n{tasks[task_num]['text']}")
        
    except ValueError:
        bot.reply_to(message, "⚠️ Введи корректный номер задачи.\nПример: /donetask 1")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")

# ========== КОМАНДА /deletetask ==========
@bot.message_handler(commands=['deletetask'])
def delete_task(message):
    try:
        parts = message.text.split(maxsplit=1)
        if len(parts) < 2:
            bot.reply_to(message, "⚠️ Укажи номер задачи.\nПример: /deletetask 1")
            return
        
        task_num = int(parts[1]) - 1
        user_id = message.from_user.id
        user_data = get_user_data(user_id)
        tasks = user_data.get('tasks', [])
        
        if task_num < 0 or task_num >= len(tasks):
            bot.reply_to(message, "❌ Задача с таким номером не найдена!")
            return
        
        deleted = tasks.pop(task_num)
        save_user_data(user_id, user_data)
        bot.reply_to(message, f"🗑️ Задача удалена:\n{deleted['text']}")
        
    except ValueError:
        bot.reply_to(message, "⚠️ Введи корректный номер задачи.\nПример: /deletetask 1")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")

# ========== КОМАНДА /notes ==========
@bot.message_handler(commands=['notes'])
def show_notes(message):
    user_id = message.from_user.id
    user_data = get_user_data(user_id)
    notes = user_data.get('notes', [])
    
    if not notes:
        bot.reply_to(message, "📭 У тебя пока нет заметок!")
        return
    
    text = "📝 *Твои заметки:*\n\n"
    for i, note in enumerate(notes, 1):
        text += f"{i}. {note.get('text', '')}\n"
        if note.get('date'):
            text += f"   📅 {note.get('date')}\n"
    
    bot.reply_to(message, text, parse_mode='Markdown')

# ========== КОМАНДА /addnote ==========
@bot.message_handler(commands=['addnote'])
def add_note(message):
    try:
        note_text = message.text.replace('/addnote', '').strip()
        if not note_text:
            bot.reply_to(message, "⚠️ Напиши заметку после команды.\nПример: /addnote Встреча в 15:00")
            return
        
        user_id = message.from_user.id
        user_data = get_user_data(user_id)
        
        if 'notes' not in user_data:
            user_data['notes'] = []
        
        user_data['notes'].append({
            'text': note_text,
            'date': datetime.now().strftime('%d.%m.%Y %H:%M')
        })
        
        save_user_data(user_id, user_data)
        bot.reply_to(message, f"✅ Заметка добавлена:\n{note_text}")
        
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")

# ========== КОМАНДА /deletenote ==========
@bot.message_handler(commands=['deletenote'])
def delete_note(message):
    try:
        parts = message.text.split(maxsplit=1)
        if len(parts) < 2:
            bot.reply_to(message, "⚠️ Укажи номер заметки.\nПример: /deletenote 1")
            return
        
        note_num = int(parts[1]) - 1
        user_id = message.from_user.id
        user_data = get_user_data(user_id)
        notes = user_data.get('notes', [])
        
        if note_num < 0 or note_num >= len(notes):
            bot.reply_to(message, "❌ Заметка с таким номером не найдена!")
            return
        
        deleted = notes.pop(note_num)
        save_user_data(user_id, user_data)
        bot.reply_to(message, f"🗑️ Заметка удалена:\n{deleted['text']}")
        
    except ValueError:
        bot.reply_to(message, "⚠️ Введи корректный номер заметки.\nПример: /deletenote 1")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")

# ========== ОБРАБОТЧИК ВСЕХ ОСТАЛЬНЫХ СООБЩЕНИЙ ==========
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, "🤔 Я не знаю такой команды.\nНапиши /start, чтобы увидеть список команд.")

# ========== ЗАПУСК БОТА ==========
if __name__ == '__main__':
    print("🔄 Запускаю polling...")
    try:
        bot.polling(none_stop=True, interval=0, timeout=20)
    except Exception as e:
        print(f"❌ Ошибка в polling: {e}")
        time.sleep(5)
        # Перезапускаем при ошибке
        os.execv(sys.executable, ['python'] + sys.argv)
else:
    # Это для запуска из web_server.py
    print("✅ Бот импортирован и готов к работе")
    # Запускаем polling в отдельном потоке
    def run_bot():
        try:
            bot.polling(none_stop=True, interval=0, timeout=20)
        except Exception as e:
            print(f"❌ Ошибка в polling: {e}")
            time.sleep(5)
    
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    print("✅ Бот запущен в фоновом потоке")
