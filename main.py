import telebot
import json
import os
from datetime import datetime
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

# ==================== КОНФИГУРАЦИЯ ====================
TOKEN = os.environ.get('BOT_TOKEN', '8609924490:AAGBFzUjXkNOWYd2GhKXmD1Dlv8S4l9A5qs')
WEB_APP_URL = os.environ.get('WEB_APP_URL', 'https://episode-unquote-oversleep.ngrok-free.dev')

bot = telebot.TeleBot(TOKEN)
bot.delete_webhook()

# Создаем папки
os.makedirs('data', exist_ok=True)
os.makedirs('languages', exist_ok=True)
os.makedirs('web_app', exist_ok=True)

# ==================== РАБОТА С ДАННЫМИ ====================
def load_data(filename, default=None):
    if default is None:
        default = {}
    path = f'data/{filename}'
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    return json.loads(content)
                return default
        except:
            return default
    return default

def save_data(filename, data):
    path = f'data/{filename}'
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_lang(lang):
    path = f'languages/{lang}.json'
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

# ==================== КОМАНДЫ БОТА ====================
@bot.message_handler(commands=['start'])
def start(message):
    user_id = str(message.chat.id)
    
    # Загружаем пользователей
    users = load_data('users.json', {})
    
    if user_id not in users:
        users[user_id] = {
            "name": message.from_user.first_name,
            "joined": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "lang": "ru",
            "notes": [],
            "tasks": []
        }
        save_data('users.json', users)
    
    # Клавиатура с кнопкой Mini App
    markup = InlineKeyboardMarkup(row_width=1)
    
    web_app_btn = InlineKeyboardButton(
        text="🚀 Открыть Органайзер",
        web_app=WebAppInfo(url=f"{WEB_APP_URL}/index.html?user_id={user_id}")
    )
    
    calendar_btn = InlineKeyboardButton(
        text="📅 Календарь",
        web_app=WebAppInfo(url=f"{WEB_APP_URL}/calendar.html?user_id={user_id}")
    )
    
    markup.add(web_app_btn, calendar_btn)
    
    bot.send_message(
        user_id,
        f"🌟 Привет, {message.from_user.first_name}!\n\n"
        f"Я твой личный органайзер. Вот что я умею:\n\n"
        f"📝 **Заметки** — сохраняй важную информацию\n"
        f"⏰ **Напоминания** — не пропускай важные события\n"
        f"📅 **Календарь** — планируй свой день\n"
        f"🏷️ **Категории** — организуй задачи по темам\n"
        f"📜 **История** — смотри что сделано\n\n"
        f"Нажми на кнопку ниже, чтобы открыть приложение!",
        parse_mode='Markdown',
        reply_markup=markup
    )

@bot.message_handler(commands=['help'])
def help_command(message):
    help_text = """
📖 *Помощь по боту*

🔹 /start — Запустить бота
🔹 /help — Показать эту справку
🔹 /notes — Мои заметки
🔹 /tasks — Мои задачи
🔹 /profile — Мой профиль

📱 *Мини-приложение*
Нажми на кнопку "Открыть Органайзер" для удобного интерфейса!

❓ По всем вопросам пишите сюда.
    """
    bot.send_message(message.chat.id, help_text, parse_mode='Markdown')

@bot.message_handler(commands=['notes'])
def show_notes(message):
    user_id = str(message.chat.id)
    users = load_data('users.json', {})
    notes = users.get(user_id, {}).get('notes', [])
    
    if not notes:
        bot.send_message(message.chat.id, "📭 У вас пока нет заметок")
        return
    
    text = "📝 *Ваши заметки:*\n\n"
    for i, note in enumerate(notes[-5:], 1):
        text += f"{i}. **{note.get('title', 'Без названия')}**\n"
        text += f"   {note.get('text', '')[:100]}\n"
        text += f"   📅 {note.get('date', '')}\n\n"
    
    bot.send_message(message.chat.id, text, parse_mode='Markdown')

@bot.message_handler(commands=['tasks'])
def show_tasks(message):
    user_id = str(message.chat.id)
    users = load_data('users.json', {})
    tasks = users.get(user_id, {}).get('tasks', [])
    active_tasks = [t for t in tasks if not t.get('completed', False)]
    
    if not active_tasks:
        bot.send_message(message.chat.id, "✅ У вас нет активных задач!")
        return
    
    text = "📋 *Активные задачи:*\n\n"
    for i, task in enumerate(active_tasks, 1):
        text += f"{i}. {task.get('title', 'Без названия')}\n"
    
    bot.send_message(message.chat.id, text, parse_mode='Markdown')

@bot.message_handler(commands=['profile'])
def profile(message):
    user_id = str(message.chat.id)
    users = load_data('users.json', {})
    user_data = users.get(user_id, {})
    
    notes_count = len(user_data.get('notes', []))
    tasks_count = len([t for t in user_data.get('tasks', []) if not t.get('completed')])
    completed_count = len([t for t in user_data.get('tasks', []) if t.get('completed')])
    
    text = f"👤 *Ваш профиль*\n\n"
    text += f"Имя: {user_data.get('name', 'Не указано')}\n"
    text += f"Дата регистрации: {user_data.get('joined', 'Неизвестно')}\n"
    text += f"📝 Заметок: {notes_count}\n"
    text += f"📋 Активных задач: {tasks_count}\n"
    text += f"✅ Выполнено задач: {completed_count}\n"
    
    bot.send_message(message.chat.id, text, parse_mode='Markdown')

@bot.message_handler(func=lambda m: True)
def echo(message):
    bot.send_message(message.chat.id, "Используйте кнопки меню или команды:\n/start, /help, /notes, /tasks, /profile")

# ==================== ЗАПУСК ====================
if __name__ == '__main__':
    print("=" * 50)
    print("🤖 Бот-органайзер запущен!")
    print("=" * 50)
    print(f"📱 Web App URL: {WEB_APP_URL}")
    print("\nДоступные команды:")
    print("  /start  - Запустить бота")
    print("  /help   - Помощь")
    print("  /notes  - Мои заметки")
    print("  /tasks  - Мои задачи")
    print("  /profile- Мой профиль")
    print("=" * 50)
    print("🚀 Бот готов к работе!")
    
    try:
        bot.infinity_polling(timeout=10)
    except Exception as e:
        print(f"Ошибка: {e}")
