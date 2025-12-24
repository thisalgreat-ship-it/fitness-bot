import os
from flask import Flask, request, abort
import telebot

# Токен берём из переменной окружения Render
TOKEN = os.getenv('TOKEN')
if not TOKEN:
    print("ОШИБКА: TOKEN не найден! Добавьте переменную TOKEN в Render.")
    exit(1)

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# ——— ВСЯ ЛОГИКА БОТА (онбординг и план) ———

users = {}

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
    bot.reply_to(message, "Привет! Я помогу тебе создать персональный план тренировок под твои цели и возможности 🔥\n\nОтветь на несколько вопросов — это займёт меньше минуты.")
    ask_question(message.chat.id)

def ask_question(chat_id):
    state = get_state(chat_id)
    step = state["step"]
    if step >= len(questions):
        generate_plan(chat_id)
        return
    q = questions[step]
    text = q["text"]
    if "options" in q:
        markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        for opt in q["options"]:
            markup.add(opt)
        bot.send_message(chat_id, text, reply_markup=markup)
    else:
        markup = telebot.types.ReplyKeyboardRemove()
        bot.send_message(chat_id, text, reply_markup=markup)

def generate_plan(chat_id):
    state = get_state(chat_id)
    data = state["data"]
    name = data.get("name", "Друг")
    plan = f"""
🏆 *Твой персональный план готов, {name}!* 🏆

🎯 Цель: {data.get("goal", "?")}
🏋️ Уровень: {data.get("level", "?")}
📅 Тренировки: {data.get("days", "?")} дней в неделю
⚖️ Рост: {data.get("height", "?")} см | Вес: {data.get("weight", "?")} кг
🩹 Ограничения: {data.get("injuries", "Нет")}

Пример недели 1:
• Понедельник: Full Body A (35 мин)
• Среда: Full Body B (40 мин)
• Пятница: Cardio + Core (30 мин)

Всё под твоё оборудование: {data.get("equipment", "только тело")}.

Готов начать? 💪
    """.strip()
    bot.send_message(chat_id, plan, parse_mode='Markdown')
    bot.send_message(chat_id, "Напиши /start, чтобы пройти заново 😊")

@bot.message_handler(func=lambda m: True)
def answer(message):
    user_id = message.chat.id
    state = get_state(user_id)
    step = state["step"]
    if step >= len(questions):
        bot.reply_to(message, "План уже готов! Напиши /start для нового.")
        return
    state["data"][questions[step]["key"]] = message.text.strip()
    state["step"] += 1
    ask_question(user_id)

# ——— WEBHOOK ———

@app.route('/')
def index():
    return "Бот работает! 💪"

@app.route('/' + TOKEN, methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    abort(403)

# ——— ЗАПУСК ———

print("Бот запущен...")

# Устанавливаем webhook один раз при старте
bot.remove_webhook()  # на всякий случай очищаем старый
# ←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←
# ЗАМЕНИ НА СВОЙ ТОЧНЫЙ URL ИЗ RENDER !!!
WEBHOOK_URL = "https://fitness-bot-0v41.onrender.com/" + TOKEN
bot.set_webhook(url=WEBHOOK_URL)
print(f"Webhook установлен: {WEBHOOK_URL}")

app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))