// Инициализация Telegram Web App
const tg = window.Telegram.WebApp;
tg.expand(); // Растягиваем на весь экран
tg.MainButton.hide();

// Получаем user_id из URL
const urlParams = new URLSearchParams(window.location.search);
const userId = urlParams.get('user_id');

// Данные пользователя
let userData = {
    tasks: [],
    notes: []
};

// Загрузка данных
async function loadUserData() {
    // Здесь должен быть запрос к вашему боту
    // Пока что демо-данные
    userData = {
        tasks: [
            { id: 1, title: 'Создать бота', completed: false },
            { id: 2, title: 'Настроить Web App', completed: true },
            { id: 3, title: 'Задеплоить на сервер', completed: false }
        ],
        notes: [
            { id: 1, title: 'Идея', text: 'Сделать синхронизацию с Google Calendar' }
        ]
    };
    
    updateStats();
    renderTasks();
    renderNotes();
}

// Обновление статистики
function updateStats() {
    const completedTasks = userData.tasks.filter(t => t.completed).length;
    document.getElementById('tasksCount').textContent = completedTasks;
    document.getElementById('notesCount').textContent = userData.notes.length;
}

// Рендер задач
function renderTasks(filter = 'all') {
    const taskList = document.getElementById('taskList');
    let filteredTasks = userData.tasks;
    
    if (filter === 'active') {
        filteredTasks = userData.tasks.filter(t => !t.completed);
    } else if (filter === 'completed') {
        filteredTasks = userData.tasks.filter(t => t.completed);
    }
    
    taskList.innerHTML = filteredTasks.map(task => `
        <div class="task-item ${task.completed ? 'completed' : ''}">
            <input type="checkbox" ${task.completed ? 'checked' : ''} 
                   onchange="toggleTask(${task.id})">
            <span>${task.title}</span>
            <button onclick="deleteTask(${task.id})" style="margin-left: auto;">🗑️</button>
        </div>
    `).join('');
}

// Переключение задачи
function toggleTask(taskId) {
    const task = userData.tasks.find(t => t.id === taskId);
    if (task) {
        task.completed = !task.completed;
        updateStats();
        renderTasks();
        
        // Отправляем данные боту
        tg.sendData(JSON.stringify({
            action: 'toggle_task',
            task_id: taskId,
            completed: task.completed
        }));
    }
}

// Добавление задачи
function addTask() {
    const input = document.getElementById('newTaskInput');
    const title = input.value.trim();
    
    if (title) {
        const newTask = {
            id: Date.now(),
            title: title,
            completed: false
        };
        userData.tasks.push(newTask);
        input.value = '';
        updateStats();
        renderTasks();
        
        tg.sendData(JSON.stringify({
            action: 'add_task',
            task: newTask
        }));
    }
}

// Рендер заметок
function renderNotes() {
    const notesList = document.getElementById('notesList');
    notesList.innerHTML = userData.notes.map(note => `
        <div class="note-item">
            <div class="note-title">${note.title}</div>
            <div class="note-text">${note.text}</div>
        </div>
    `).join('');
}

// Добавление заметки
function addNote() {
    const title = document.getElementById('newNoteTitle').value.trim();
    const text = document.getElementById('newNoteText').value.trim();
    
    if (title && text) {
        const newNote = {
            id: Date.now(),
            title: title,
            text: text
        };
        userData.notes.push(newNote);
        document.getElementById('newNoteTitle').value = '';
        document.getElementById('newNoteText').value = '';
        updateStats();
        renderNotes();
        
        tg.sendData(JSON.stringify({
            action: 'add_note',
            note: newNote
        }));
    }
}

// Рендер календаря
function renderCalendar(year, month) {
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const startingDay = firstDay.getDay() || 7; // Понедельник как первый день
    
    const days = [];
    for (let i = 1; i < startingDay; i++) {
        days.push('<div class="calendar-day"></div>');
    }
    
    for (let i = 1; i <= lastDay.getDate(); i++) {
        const isToday = i === new Date().getDate() && 
                       month === new Date().getMonth() && 
                       year === new Date().getFullYear();
        days.push(`
            <div class="calendar-day ${isToday ? 'today' : ''}" onclick="selectDay(${i})">
                ${i}
            </div>
        `);
    }
    
    document.getElementById('calendarDays').innerHTML = days.join('');
}

// Инициализация календаря
let currentDate = new Date();
renderCalendar(currentDate.getFullYear(), currentDate.getMonth());

// Навигация по месяцам
document.getElementById('prevMonth')?.addEventListener('click', () => {
    currentDate.setMonth(currentDate.getMonth() - 1);
    renderCalendar(currentDate.getFullYear(), currentDate.getMonth());
    document.getElementById('monthYear').textContent = 
        currentDate.toLocaleString('ru', { month: 'long', year: 'numeric' });
});

document.getElementById('nextMonth')?.addEventListener('click', () => {
    currentDate.setMonth(currentDate.getMonth() + 1);
    renderCalendar(currentDate.getFullYear(), currentDate.getMonth());
    document.getElementById('monthYear').textContent = 
        currentDate.toLocaleString('ru', { month: 'long', year: 'numeric' });
});

// Переключение вкладок
document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
        const tabId = tab.dataset.tab;
        
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        
        tab.classList.add('active');
        document.getElementById(tabId).classList.add('active');
    });
});

// Фильтры задач
document.querySelectorAll('.filter').forEach(filter => {
    filter.addEventListener('click', () => {
        const filterValue = filter.dataset.filter;
        
        document.querySelectorAll('.filter').forEach(f => f.classList.remove('active'));
        filter.classList.add('active');
        
        renderTasks(filterValue);
    });
});

// Кнопки добавления
document.getElementById('addTaskBtn')?.addEventListener('click', addTask);
document.getElementById('addNoteBtn')?.addEventListener('click', addNote);
document.getElementById('newTaskInput')?.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') addTask();
});

// Инициализация
loadUserData();

// Настройка темы Telegram
tg.onEvent('themeChanged', () => {
    document.body.style.backgroundColor = tg.themeParams.bg_color;
});