from flask import Flask, send_from_directory, request, jsonify
from flask_cors import CORS
import json
import os

app = Flask(__name__, static_folder='web_app')
CORS(app)

# Создаем папки
os.makedirs('data', exist_ok=True)
os.makedirs('web_app', exist_ok=True)

# Middleware для обхода предупреждения ngrok
@app.before_request
def skip_ngrok_warning():
    if request.headers.get('User-Agent') and 'ngrok' not in request.headers.get('User-Agent', ''):
        pass

def load_users():
    path = 'data/users.json'
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    return json.loads(content)
                return {}
        except:
            return {}
    return {}

def save_users(users):
    with open('data/users.json', 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

@app.route('/')
def index():
    return send_from_directory('web_app', 'index.html')

@app.route('/index.html')
def index_html():
    return send_from_directory('web_app', 'index.html')

@app.route('/calendar.html')
def calendar_html():
    return send_from_directory('web_app', 'calendar.html')

@app.route('/style.css')
def style_css():
    return send_from_directory('web_app', 'style.css')

@app.route('/script.js')
def script_js():
    return send_from_directory('web_app', 'script.js')

@app.route('/api/user/<user_id>', methods=['GET'])
def get_user_data(user_id):
    users = load_users()
    user_data = users.get(user_id, {})
    return jsonify({
        'name': user_data.get('name', ''),
        'notes': user_data.get('notes', []),
        'tasks': user_data.get('tasks', [])
    })

@app.route('/api/user/<user_id>', methods=['POST'])
def save_user_data(user_id):
    data = request.json
    users = load_users()
    
    if user_id not in users:
        users[user_id] = {}
    
    if 'notes' in data:
        users[user_id]['notes'] = data['notes']
    if 'tasks' in data:
        users[user_id]['tasks'] = data['tasks']
    if 'name' in data:
        users[user_id]['name'] = data['name']
    
    save_users(users)
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Веб-сервер запущен на порту {port}")
    app.run(host='0.0.0.0', port=port)