import telebot
import json
import os
from datetime import datetime
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from github import Github

# ==================== КОНФИГУРАЦИЯ ====================
TOKEN = os.environ.get('BOT_TOKEN', '8609924490:AAGBFzUjXkNOWYd2GhKXmD1Dlv8S4l9A5qs')
WEB_APP_URL = os.environ.get('WEB_APP_URL', 'https://your-app.up.railway.app')

# GitHub настройки
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
GITHUB_REPO = os.environ.get('GITHUB_REPO', 'sirunchik/Taskybot')
REPO_PATH = 'data/users.json'  # Путь к файлу в репозитории

bot = telebot.TeleBot(TOKEN)
bot.delete_webhook()

# Создаем локальные папки
os.makedirs('data', exist_ok=True)
os.makedirs('languages', exist_ok=True)
os.makedirs('web_app', exist_ok=True)

# ==================== РАБОТА С GITHUB ====================
def load_users_from_github():
    """Загружает users.json из GitHub репозитория"""
    try:
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(GITHUB_REPO)
        
        # Пытаемся получить файл
        try:
            contents = repo.get_contents(REPO_PATH)
            import base64
            content = base64.b64decode(contents.content).decode('utf-8')
            return json.loads(content)
        except:
            # Файла нет — создаём пустой
            print("Файл users.json не найден в репозитории, создаю новый")
            return {}
    except Exception as e:
        print(f"Ошибка загрузки из GitHub: {e}")
        # Пробуем загрузить локально
        return load_users_local()

def save_users_to_github(users):
    """Сохраняет users.json в GitHub репозиторий"""
    try:
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(GITHUB_REPO)
        
        content = json.dumps(users, ensure_ascii=False, indent=2)
        import base64
        encoded = base64.b64encode(content.encode('utf-8')).decode('utf-8')
        
        # Пытаемся обновить существующий файл
        try:
            contents = repo.get_contents(REPO_PATH)
            repo.update_file(contents.path, "Обновление данных бота", content, contents.sha)
        except:
            # Создаём новый файл
            repo.create_file(REPO_PATH, "Создание файла данных бота", content)
        
        print("✅ Данные сохранены для вашего удобства")
        return True
    except Exception as e:
        print(f"❌ Ошибка сохранения в GitHub: {e}")
        return False

def load_users_local():
    """Резервная загрузка из локального файла"""
    path = 'data/users.json'
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    return json.loads(content)
        except:
            pass
    return {}

def save_users_local(users):
    """Резервное сохранение в локальный файл"""
    path = 'data/users.json'
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

# Загружаем данные (сначала из GitHub, потом локально)
users = load_users_from_github()
if not users:
    users = load_users_local()

def save_users(users):
    """Сохраняет пользователей и в GitHub, и локально"""
    save_users_local(users)
    save_users_to_github(users)

def load_data(filename, default=None):
    """Загружает другие JSON файлы (локально)"""
    if default is None:
        default = {}
    path = f'data/{filename}'
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    return json.loads(content)
        except:
            pass
    return default

def save_data(filename, data):
    """Сохраняет другие JSON файлы (локально)"""
    path = f'data/{filename}'
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ==================== КОМАНДЫ БОТА ====================
@bot.message_handler(commands=['start'])
def start(message):
    user_id = str(message.chat.id)
    
    if user_id not in users:
        users[user_id] = {
            "name": message.from_user.first_name,
            "joined": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "lang": "ru",
            "notes": [],
            "tasks": []
        }
        save_users(users)
    
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
        f"📱 Твой личный органайзер!\n\n"
        f"📝 Заметки\n"
        f"✅ Задачи\n"
        f"📅 Календарь с напоминаниями\n\n"
        f"Все данные сохраняются в GitHub — они не пропадут!",
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
Нажми на кнопку "Открыть Органайзер"

💾 *Данные сохраняются в GitHub — безопасно и надёжно!*
    """
    bot.send_message(message.chat.id, help_text, parse_mode='Markdown')

@bot.message_handler(commands=['notes'])
def show_notes(message):
    user_id = str(message.chat.id)
    user_data = users.get(user_id, {})
    notes = user_data.get('notes', [])
    
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
    user_data = users.get(user_id, {})
    tasks = user_data.get('tasks', [])
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
    user_data = users.get(user_id, {})
    
    notes_count = len(user_data.get('notes', []))
    tasks = user_data.get('tasks', [])
    tasks_count = len([t for t in tasks if not t.get('completed')])
    completed_count = len([t for t in tasks if t.get('completed')])
    
    text = f"👤 *Ваш профиль*\n\n"
    text += f"Имя: {user_data.get('name', 'Не указано')}\n"
    text += f"Дата регистрации: {user_data.get('joined', 'Неизвестно')}\n"
    text += f"📝 Заметок: {notes_count}\n"
    text += f"📋 Активных задач: {tasks_count}\n"
    text += f"✅ Выполнено задач: {completed_count}\n"
    text += f"\n💾 Данные хранятся в GitHub"
    
    bot.send_message(message.chat.id, text, parse_mode='Markdown')

@bot.message_handler(func=lambda m: True)
def echo(message):
    bot.send_message(message.chat.id, "Используйте команды:\n/start, /help, /notes, /tasks, /profile")

# ==================== ЗАПУСК ====================
if __name__ == '__main__':
    print("=" * 50)
    print("🤖 Бот-органайзер запущен!")
    print("=" * 50)
    print(f"📱 Web App URL: {WEB_APP_URL}")
    print("💾 Данные сохраняются в GitHub")
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
