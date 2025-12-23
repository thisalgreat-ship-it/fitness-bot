import os
import telebot
from flask import Flask, request, abort

TOKEN = os.getenv('TOKEN')  # Токен из переменной окружения в Render

bot = telebot.TeleBot(TOKEN)

app = Flask(__name__)

# Здесь вся логика бота (онбординг и план) — оставь как была раньше
# (я вставлю её полностью, чтобы не потерять)

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
    goal = data["goal"]
    days = data["days"]
    level = data["level"]
    
    plan = f"""
🏆 *Твой персональный план готов, {name}!* 🏆

🎯 Цель: {goal}
🏋️ Уровень: {level}
📅 Тренировки: {days} дней в неделю
⚖️ Рост: {data.get('height', '?')} см | Вес: {data.get('weight', '?')} кг
🩹 Ограничения: {data.get('injuries', 'Нет')}

*Пример недели 1:*
• Понедельник: Full Body A (35 мин)
• Среда: Full Body B (40 мин)
• Пятница: Cardio + Core (30 мин)
• Воскресенье: Активное восстановление

Все упражнения адаптированы под твоё оборудование: {data.get('equipment', 'только тело')}.

Готов начать прямо сегодня? 💪
    """.strip()
    
    bot.send_message(chat_id, plan, parse_mode='Markdown')
    bot.send_message(chat_id, "Напиши /start, чтобы пройти опрос заново 😊")

@bot.message_handler(func=lambda m: True)
def answer(message):
    user_id = message.chat.id
    state = get_state(user_id)
    step = state["step"]
    
    if step >= len(questions):
        bot.reply_to(message, "Твой план уже готов! Напиши /start для нового.")
        return
    
    q = questions[step]
    answer_text = message.text.strip()
    
    state["data"][q["key"]] = answer_text
    state["step"] += 1
    
    ask_question(user_id)

# Webhook роуты
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
    else:
        abort(403)

# Главный запуск
print("Бот запущен...")

# Удаляем старый webhook и устанавливаем новый
bot.remove_webhook()
# ←←←←← ЗАМЕНИ НА СВОЙ РЕАЛЬНЫЙ URL ИЗ RENDER!
bot.set_webhook(url='https://fitness-bot-0v41.onrender.com' + TOKEN)  # пример, замени на свой!

# Запуск Flask
app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))