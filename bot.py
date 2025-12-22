# Файл: bot.py
import os
import telebot as telebot  # не меняем, но проверь
import json
import os

# ВСТАВЬ СЮДА СВОЙ ТОКЕН ОТ BOTFATHER
TOKEN = os.getenv('TOKEN')

bot = telebot.TeleBot(TOKEN)

# Файл для хранения данных пользователей (вместо базы данных на старте)
DATA_FILE = 'users.json'

# Загружаем данные, если файл существует
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        users = json.load(f)
else:
    users = {}

# Вопросы для онбординга
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

def get_user_state(user_id):
    return users.get(str(user_id), {"step": 0, "data": {}})

def save_user_state(user_id, state):
    users[str(user_id)] = state
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    users[str(user_id)] = {"step": 0, "data": {}}
    save_user_state(user_id, users[str(user_id)])
    bot.reply_to(message, "Привет! Я помогу тебе создать персональный план тренировок под твои цели и возможности 🔥\n\nОтветь на несколько вопросов — это займёт меньше минуты.")
    ask_question(message.chat.id)

def ask_question(chat_id):
    state = get_user_state(chat_id)
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
    state = get_user_state(chat_id)
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

Я буду напоминать о тренировках и корректировать план по твоей обратной связи 💪

Готов начать прямо сегодня?
    """.strip()
    
    bot.send_message(chat_id, plan, parse_mode='Markdown')
    bot.send_message(chat_id, "Напиши /start, чтобы пройти опрос заново или создать план для друга 😊")

@bot.message_handler(func=lambda m: True)
def answer(message):
    user_id = message.chat.id
    state = get_user_state(user_id)
    step = state["step"]
    
    if step >= len(questions):
        bot.reply_to(message, "Твой план уже готов! Напиши /start для нового.")
        return
    
    q = questions[step]
    answer = message.text.strip()
    
    state["data"][q["key"]] = answer
    state["step"] += 1
    save_user_state(user_id, state)
    
    ask_question(user_id)

print("Бот запущен...")
bot.infinity_polling()