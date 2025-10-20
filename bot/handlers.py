import logging
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.keyboards import (
    get_cancel_keyboard,
    get_main_menu,
    get_habits_keyboard,
    get_check_habits_keyboard
)
from database.db import Database

logger = logging.getLogger(__name__)

router = Router()

db = Database()

class HabitStates(StatesGroup):
    waiting_for_habit_name = State()

@router.message(CommandStart())
async def cmd_start(message: Message):
    user_id = message.from_user.id
    user_name = message.from_user.username or message.from_user.first_name
    logger.info(f"Пользователь {message.from_user.id} нажал /start")
    db.add_user(user_id, user_name)

    await message.answer(f"👋 Привет, {message.from_user.first_name}!\n\n"
        "Я помогу тебе отслеживать привычки.\n\n"
        "Используй кнопки ниже для управления:", reply_markup=get_main_menu())

@router.message(F.text == "➕ Добавить привычку")
async def button_add_habit(message: Message, state: FSMContext):
    logger.info(f"Пользователь {message.from_user.id} нажал 'Добавить привычку'")
    await message.answer("📝 Введите название новой привычки:\n\n"
        "Например: Пить воду, Делать зарядку, Читать книгу", reply_markup=get_cancel_keyboard())
    await state.set_state(HabitStates.waiting_for_habit_name)

@router.message(HabitStates.waiting_for_habit_name, F.text != "❌ Отмена")
async def process_habit_name(message: Message, state: FSMContext):
    habit_name = message.text.strip()
    user_id = message.from_user.id

    if len(habit_name) < 2:
        await message.answer(
            "❌ Название слишком длинное (максимум 100 символов).\n"
            "Попробуйте еще раз:"
        )
        return
    if len(habit_name) > 100:
        await message.answer(
            "❌ Название слишком длинное (максимум 100 символов).\n"
            "Попробуйте еще раз:"
        )
        return

    db.add_habit(user_id, habit_name)

    await message.answer(
        f"✅ Привычка '{habit_name}' успешно добавлена!",
        reply_markup=get_main_menu()
    )
    await state.clear()

@router.message(F.text == "❌ Отмена")
async def button_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Действие отменено", reply_markup=get_main_menu())


@router.message(F.text == "❌ Удалить привычку")
async def button_delete_habit(message: Message):
    user_id = message.from_user.id
    habits = db.get_all_habits(user_id)

    if not habits:
        await message.answer("📋 У вас пока нет привычек.\n"
                             "Добавьте первую с помощью кнопки '➕ Добавить привычку'", reply_markup=get_main_menu())
        return

    await message.answer("❌ Выберите привычку, которую хотите удалить:\n", reply_markup=get_habits_keyboard(habits))

@router.message(F.text == "📋 Мои привычки")
async def button_list_habits(message: Message):
    user_id = message.from_user.id
    habits = db.get_all_habits(user_id)

    if not habits:
        await message.answer("📋 У вас пока нет привычек.\n"
            "Добавьте первую с помощью кнопки '➕ Добавить привычку'", reply_markup=get_main_menu())
        return


    text = "📋 Ваши привычки:\n\n"
    for idx, habit in enumerate(habits, 1):
        habit_id, name, created_at = habit
        text += f"{idx}. {name}\n"

    await message.answer(text, reply_markup=get_main_menu())

@router.message(F.text == "✅ Отметить выполнение")
async def button_check_habits(message: Message):
    user_id = message.from_user.id
    habits = db.get_all_habits(user_id)

    if not habits:
        await message.answer("📋 У вас пока нет привычек.\n"
                             "Добавьте первую с помощью кнопки '➕ Добавить привычку'", reply_markup=get_main_menu())
        return

    completed_today = []
    for habit in habits:
        habit_id = habit[0]
        if db.is_habit_done_today(habit_id):
            completed_today.append(habit_id)

    await message.answer("✅ Отметьте выполненные сегодня привычки:\n\n"
        "⭕ - не выполнена\n"
        "✅ - выполнена", reply_markup=get_check_habits_keyboard(habits, completed_today))


@router.callback_query(F.data.startswith("check_"))
async def callback_check_habits(callback: CallbackQuery):
    habit_id = int(callback.data.split("_")[1])
    user_id = callback.from_user.id

    # принадлежит ли привычка пользователю
    user_habits = db.get_all_habits(user_id)
    user_habit_ids = [h[0] for h in user_habits]
    if habit_id not in user_habit_ids:
        await callback.answer("❌ Эта привычка вам не принадлежит", show_alert=True)
        return

    # название привычки
    habit_name = None
    for habit in user_habits:
        if habit[0] == habit_id:
            habit_name = habit[1]
            break

    if db.is_habit_done_today(habit_id):
        await callback.answer("ℹ️ Эта привычка уже отмечена сегодня", show_alert=True)
        return

    db.mark_habit_done(habit_id)

    habits = db.get_all_habits(user_id)
    completed_today = []
    for habit in habits:
        if db.is_habit_done_today(habit[0]):
            completed_today.append(habit[0])

    await callback.message.edit_reply_markup(reply_markup=get_check_habits_keyboard(habits, completed_today))

    await callback.answer(f"🎉 Отлично! '{habit_name}' выполнена!")

@router.callback_query(F.data.startswith("uncheck_"))
async def callback_uncheck_habits(callback: CallbackQuery):
    habit_id = int(callback.data.split("_")[1])
    user_id = callback.from_user.id

    # принадлежит ли пользователю
    user_habits = db.get_all_habits(user_id)
    user_habits_ids = [h[0] for h in user_habits]
    if habit_id not in user_habits_ids:
        await callback.answer("❌ Эта привычка вам не принадлежит", show_alert=True)
        return

    # получаем название привычки
    habit_name = None
    for habit in user_habits:
        if habit[0] == habit_id:
            habit_name = habit[1]
            break

    if not db.is_habit_done_today(habit_id):
        await callback.answer("ℹ️ Эта привычка не была отмечена сегодня", show_alert=True)
        return

    db.mark_habit_not_done(habit_id)

    habits = db.get_all_habits(user_id)
    completed_today = []
    for habit in habits:
        if db.is_habit_done_today(habit[0]):
            completed_today.append(habit[0])

    await callback.message.edit_reply_markup(reply_markup=get_check_habits_keyboard(habits, completed_today))

    await callback.answer(f"↩️ Отметка для '{habit_name}' отменена")

@router.message(F.text == "❓ Помощь")
async def button_help(message: Message):
    await message.answer("📖 Как использовать бота:\n\n"
        "➕ Добавить привычку - создать новую привычку\n"
        "📋 Мои привычки - посмотреть список всех привычек\n"
        "✅ Отметить выполнение - отметить выполненные сегодня\n"
        "❓ Помощь - показать эту справку\n\n"
        "💡 Совет: Отмечайте привычки каждый день, "
        "чтобы не терять прогресс!", reply_markup=get_main_menu())


@router.callback_query(F.data.startswith("delete_"))
async def callback_delete_habit(callback: CallbackQuery):
    habit_id = int(callback.data.split("_")[1])
    user_id = callback.from_user.id

    # принадлежит ли пользователю
    user_habits = db.get_all_habits(user_id)
    user_habits_ids = [h[0] for h in user_habits]
    if habit_id not in user_habits_ids:
        await callback.answer("❌ Эта привычка вам не принадлежит", show_alert=True)
        return

    # получаем название привычки
    habit_name = None
    for habit in user_habits:
        if habit[0] == habit_id:
            habit_name = habit[1]
            break

    db.delete_habit(habit_id, user_id)
    habits_after_delete = db.get_all_habits(user_id)
    if len(habits_after_delete) == 0:

        await callback.message.edit_text("📋 У вас больше нет привычек.\n"
            "Добавьте новую с помощью кнопки '➕ Добавить привычку'", reply_markup=None)
    else:
        db.delete_habit(habit_id, user_id)
        habits = db.get_all_habits(user_id)
        await callback.message.edit_reply_markup(reply_markup=get_habits_keyboard(habits))

    await callback.answer(f"❌ Привычка '{habit_name}' удалена")