from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup


def get_main_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="➕ Добавить привычку"),
                KeyboardButton(text ="❌ Удалить привычку"),
                KeyboardButton(text="📋 Мои привычки")
            ],
            [
                KeyboardButton(text="✅ Отметить выполнение"),
                KeyboardButton(text="❓ Помощь")
            ]
        ], resize_keyboard=True
    )

    return keyboard

def get_habits_keyboard(habits):
    buttons = []
    for habit in habits:
        habit_id = habit[0]
        habit_name = habit[1]

        button = InlineKeyboardButton(text=habit_name, callback_data=f"delete_{habit_id}")
        buttons.append([button])
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard

def get_check_habits_keyboard(habits, completed_today):
    buttons = []

    for habit in habits:
        habit_id = habit[0]
        habit_name = habit[1]

        if habit_id in completed_today:
            text = f"✅ {habit_name}"
            callback_data = f"uncheck_{habit_id}"
        else:
            text = f"⭕ {habit_name}"
            callback_data = f"check_{habit_id}"

        button = InlineKeyboardButton(text=text, callback_data=callback_data)
        buttons.append([button])
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard

def get_cancel_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❌ Отмена")]
        ], resize_keyboard=True
    )
    return keyboard





