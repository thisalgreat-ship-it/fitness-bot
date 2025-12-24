import os
from flask import Flask, request, abort
import telebot
import requests

# Переменные из Render
TOKEN = os.getenv('TOKEN')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

if not TOKEN:
    print("ОШИБКА: TOKEN от Telegram не найден")
    exit(1)

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Состояния пользователей
users = {}

# Вопросы
questions = [
    {"text": "Привет! 💪 Я твой ИИ-фитнес-тренер.\nКак тебя зовут?", "key": "name"},
    {"text": "Твой пол?", "key": "gender", "options": ["Мужской", "Женский"]},
    {"text": "Сколько тебе лет?", "key": "age"},
    {"text": "Твой рост в см?", "key": "height"},
    {"text": "Твой текущий вес в кг?", "key": "weight"},
    {"text": "Какая главная цель? 🏆", "key": "goal", "options": ["Похудеть", "Набрать массу", "Подтянуть тонус", "Улучшить выносливость"]},
    {"text": "Сколько дней в неделю можешь тренироваться?", "key": "days", "options": ["2", "3", "4", "5", "6"]},
    {"text": "Твой уровень подготовки?", "key": "level", "options": ["Новичок", "Средний", "Продвинутый"]},
    {"text": "Есть ли травмы или ограничения?\n(Напиши 'Нет', если всё ок)", "key": "injuries"},
    {"text": "Какое оборудование есть дома?", "key": "equipment", "options": ["Только тело", "Гантели", "Турник", "Коврик", "Всё есть"]},
]

def get_state(user_id):
    if str(user_id) not in users:
        users[str(user_id)] = {"step": 0, "data": {}}
    return users[str(user_id)]

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    users[str(user_id)] = {"step": 0, "data": {}}
    bot.send_message(message.chat.id, "Привет! Я создам тебе персональный план тренировок с помощью мощного ИИ 🔥\n\nОтветь на несколько вопросов:")
    ask_question(message.chat.id)

def ask_question(chat_id):
    state = get_state(chat_id)
    if state["step"] >= len(questions):
        generate_plan(chat_id)
        return
    q = questions[state["step"]]
    text = q["text"]
    if "options" in q:
        markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        for opt in q["options"]:
            markup.add(opt)
        bot.send_message(chat_id, text, reply_markup=markup)
    else:
        bot.send_message(chat_id, text, reply_markup=telebot.types.ReplyKeyboardRemove())

def generate_plan(chat_id):
    state = get_state(chat_id)
    data = state["data"]

    prompt = f"""
Ты — лучший русский фитнес-тренер. Создай подробный план тренировок на 4 недели для клиента.

Данные:
- Имя: {data.get('name', 'Друг')}
- Пол: {data.get('gender', '?')}
- Возраст: {data.get('age', '?')} лет
- Рост: {data.get('height', '?')} см
- Вес: {data.get('weight', '?')} кг
- Цель: {data.get('goal', '?')}
- Дней в неделю: {data.get('days', '?')}
- Уровень: {data.get('level', '?')}
- Травмы: {data.get('injuries', 'Нет')}
- Оборудование: {data.get('equipment', 'Только тело')}

План:
- На русском языке
- 30–45 минут на тренировку
- С прогрессией по неделям
- Конкретные упражнения с подходами и повторениями
- Мотивирующий стиль
- Формат Markdown с эмодзи и списками

Начни с приветствия по имени. Ответь только планом.
    """.strip()

    if not GROQ_API_KEY:
        bot.send_message(chat_id, "ИИ не настроен на сервере 😅\nПока простой план:\nЦель: " + data.get('goal', '?'))
        bot.send_message(chat_id, "Напиши /start для нового")
        return

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama3-8b-8192",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": 1200
            },
            timeout=25
        )

        if response.status_code == 200:
            plan = response.json()["choices"][0]["message"]["content"].strip()
            bot.send_message(chat_id, plan, parse_mode='Markdown')
        else:
            bot.send_message(chat_id, f"ИИ временно недоступен (ошибка {response.status_code}). Попробуй через 5 минут!")
    except Exception as e:
        bot.send_message(chat_id, "Проблема с подключением к ИИ. Скоро всё заработает! 💪")

    bot.send_message(chat_id, "Напиши /start, если хочешь новый план 😊")

@bot.message_handler(func=lambda m: True)
def answer(message):
    user_id = message.chat.id
    state = get_state(user_id)
    if state["step"] >= len(questions):
        bot.send_message(user_id, "План уже готов! Напиши /start для нового.")
        return
    state["data"][questions[state["step"]]["key"]] = message.text.strip()
    state["step"] += 1
    ask_question(user_id)

# Webhook
@app.route('/')
def index():
    return "Бот работает! 💪"

@app.route('/' + TOKEN, methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        update = telebot.types.Update.de_json(request.get_data().decode('utf-8'))
        bot.process_new_updates([update])
        return ''
    abort(403)

print("Бот запущен...")
bot.remove_webhook()
bot.set_webhook(url="https://fitness-bot-0v41.onrender.com/" + TOKEN)
print("Webhook установлен")

app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))