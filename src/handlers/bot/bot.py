import datetime
import tempfile
import uuid
from typing import Optional, Union

import email_validator.validate_email
import phonenumbers
from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.state import (
    StatesGroup,
    State,
)
from aiogram.fsm.context import (
    FSMContext,
)
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from handlers.bot.utils import create_start_kb
from models import User
from recognizer import recognizer
from settings import settings
from storage import (
    storage,
)
from gpt import (
    llm,
)


class UserState(StatesGroup):
    choose_city_state = State()
    type_phone_state = State()
    type_email_state = State()
    type_first_name_state = State()
    type_last_name_state = State()
    wait_for_llm_question = State()


router = Router(name=__name__)


# Обработка стартовой страницы бота
@router.message(Command("start"))
@router.callback_query(lambda query: query.data == "back_to_start")
async def start(message: Union[types.Message, types.CallbackQuery], state: FSMContext, user: Optional[User]):
    if isinstance(message, types.Message) and message.text is None:
        await message.answer("Вы не ввели текстовое сообщение")
        return
    user_id = message.from_user.id
    if isinstance(message, types.CallbackQuery):
        await message.answer()
        message = message.message
    if user is not None:
        # Отправляем меню пользователю если он уже зарегистрирован
        kb = create_start_kb(user_id in settings.tg_user_id_admins)
        await message.answer("Меню", reply_markup=kb)
        return
    # Запрашиваем город если пользователь не зарегистрирован
    await state.set_state(UserState.choose_city_state)
    await message.answer("Напиши из какого ты города")


# Обрабатываем город пользователя
@router.message(UserState.choose_city_state)
async def answer_choose_city_handler(message: types.Message, state: FSMContext, user: Optional[User]):
    if message.text is None:
        message.answer("Вы не ввели текстовое сообщение")
        return
    if user is not None:
        storage.update_tg_user_city(message.from_user.id, message.text)
        await message.answer("Вы сменили свой город.")
        await state.clear()
        return
    # Спрашиваем телефон пользователя
    await state.set_data({"city": message.text})
    await state.set_state(UserState.type_phone_state)
    await message.answer("Пожалуйста, введи свой номер телефона в формате +71234567890")


# Обрабатываем телефон пользователя
@router.message(UserState.type_phone_state)
async def answer_type_phone_handler(message: types.Message, state: FSMContext, user: Optional[User]):
    if message.text is None:
        message.answer("Вы не ввели текстовое сообщение")
        return
    try:
        # Валидируем ввод пользователя
        phone = phonenumbers.format_number(phonenumbers.parse(message.text, None), phonenumbers.PhoneNumberFormat.E164)
    except phonenumbers.NumberParseException:
        await message.answer("Вы неправильно ввели номер телефона, пожалуйста, введите его в формате +71234567890")
        return
    if user is not None:
        storage.update_tg_user_phone(message.from_user.id, phone)
        await message.answer("Вы сменили свой телефон")
        await state.clear()
        return
    # Спрашиваем email пользователя
    data = await state.get_data()
    await state.set_data({"phone": phone, **data})
    await state.set_state(UserState.type_email_state)
    await message.answer("Пожалуйста, введи свой email. Формат example@example.com")


# Обрабатываем почту пользователя
@router.message(UserState.type_email_state)
async def answer_type_email_handler(message: types.Message, state: FSMContext, user: Optional[User]):
    if message.text is None:
        message.answer("Вы не ввели текстовое сообщение")
        return
    try:
        # Валидируем почту
        email_validator.validate_email(message.text)
    except email_validator.EmailNotValidError:
        await message.answer("Вы неправильно ввели свой email. Формат example@example.com")
        return
    if user is not None:
        storage.update_tg_user_email(message.from_user.id, message.text)
        await message.answer("Вы сменили свой email")
        await state.clear()
        return
    # Спрашиваем имя пользователя
    data = await state.get_data()
    await state.set_data({"email": message.text, **data})
    await state.set_state(UserState.type_first_name_state)
    await message.answer("Пожалуйста, введи свое имя")


# Обрабатываем имя пользователя
@router.message(UserState.type_first_name_state)
async def answer_type_first_name_handler(message: types.Message, state: FSMContext, user: Optional[User]):
    if message.text is None:
        message.answer("Вы не ввели текстовое сообщение")
        return
    if user is not None:
        storage.update_tg_user_first_name(message.from_user.id, message.text)
        await message.answer("Вы сменили свой имя.")
        await state.clear()
        return
    # Спрашиваем фамилия пользователя
    data = await state.get_data()
    await state.set_data({"first_name": message.text, **data})
    await state.set_state(UserState.type_last_name_state)
    await message.answer("Пожалуйста, введи свою фамилию")


# Обрабатываем фамилию пользователя
@router.message(UserState.type_last_name_state)
async def answer_type_last_name_handler(message: types.Message, state: FSMContext, user: Optional[User]):
    if message.text is None:
        message.answer("Вы не ввели текстовое сообщение")
        return
    if user is not None:
        storage.update_tg_user_last_name(message.from_user.id, message.text)
        await message.answer("Вы сменили свою фамилию.")
        await state.clear()
        return
    data = await state.get_data()
    # Создаем пользователя в бд
    storage.create_tg_user(
        message.from_user.id,
        data["city"],
        data["phone"],
        data["email"],
        data["first_name"],
        message.text,
    )
    await message.answer("Поздравляю! Вы зарегистрированы в нашей системе")
    await state.clear()
    # Отправляем его в меню
    kb = create_start_kb(message.from_user.id in settings.tg_user_id_admins)
    await message.answer("Меню", reply_markup=kb)


# Обрабатываем случай когда пользователя хочет что то спросить
@router.message(Command("ask"))
@router.callback_query(lambda query: query.data == "ask")
async def ask_llm(
    message: Union[types.Message, types.CallbackQuery],
    state: FSMContext,
):
    if isinstance(message, types.CallbackQuery):
        await message.answer()
        message = message.message
    await message.answer("Отправь вопрос, на который хочешь получить ответ, либо запиши голосовое сообщение с вопросом")
    await state.set_state(UserState.wait_for_llm_question)


# Получаем вопрос от пользователя
@router.message(UserState.wait_for_llm_question)
async def answer_question_with_llm(
    message: types.Message,
    state: FSMContext,
):
    if message.voice is not None:
        if message.voice.duration > 10:
            await message.answer("Слишком длинный вопрос :( . Максимальная длина 10 секунд")
            return
        # Trying to translate audio to text
        # Пробуем дешифровать голсовое сообщения пользователя если он его отправил
        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as file:
            await message.bot.download(message.voice.file_id, file.name)
            text = await recognizer.recognize(file.name, format_audio="oggopus")
            await message.answer("Распознанный текст:\n{}".format(text))
    elif message.text is not None:
        text = message.text
    else:
        message.answer("Вы отправили ни текстовое, ни голосовое сообщение")
        return
    # Получаем ответ от YandexGPT и отправляем его пользователю
    answer = await llm.ask(text)
    await message.answer(answer)
    await state.clear()


# Обрабатываем случай вызова настроек от пользователя
@router.message(Command("settings"))
@router.callback_query(lambda query: query.data == "settings")
async def settings_callback(message: Union[types.Message, types.CallbackQuery]):
    if isinstance(message, types.CallbackQuery):
        await message.answer()
        message = message.message
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Поменять город", callback_data="settings_change_city")],
            [InlineKeyboardButton(text="Поменять телефон", callback_data="settings_change_phone")],
            [InlineKeyboardButton(text="Поменять email", callback_data="settings_change_email")],
            [InlineKeyboardButton(text="Поменять имя", callback_data="settings_change_first_name")],
            [InlineKeyboardButton(text="Поменять фамилию", callback_data="settings_change_last_name")],
            [InlineKeyboardButton(text="Назад", callback_data="back_to_start")],
        ]
    )
    await message.answer("Выберите, что хотите сделать", reply_markup=kb)


# Обрабатываем случай когда пользовател хочет что то поменять
@router.callback_query(lambda query: query.data.startswith("settings_change_"))
async def settings_change_callback(query: types.CallbackQuery, state: FSMContext):
    if query.message is None or query.data is None:
        return
    await query.answer()
    match "_".join(query.data.split("_")[2:]):
        case "city":
            await query.message.answer("Введите свой новый город")
            await state.set_state(UserState.choose_city_state)
        case "phone":
            await query.message.answer("Введите свой новый телефон")
            await state.set_state(UserState.type_phone_state)
        case "email":
            await query.message.answer("Введите свой новый email")
            await state.set_state(UserState.type_email_state)
        case "first_name":
            await query.message.answer("Введите свой новое имя")
            await state.set_state(UserState.type_first_name_state)
        case "last_name":
            await query.message.answer("Введите свою новую фамилию")
            await state.set_state(UserState.type_last_name_state)
        case _:
            await query.message.answer("Не знаем, что вы хотите изменить :(")


# Обрабатываем случай вызова админки бота
@router.message(Command("admin"))
@router.callback_query(lambda query: query.data == "admin_panel")
async def admin(message: Union[types.Message, types.CallbackQuery]):
    user_id = message.from_user.id
    if isinstance(message, types.CallbackQuery):
        await message.answer()
        message = message.message

    if user_id not in settings.tg_user_id_admins:
        return

    # Add 1 hour to current time, so token will be valid for 1 hour
    # Создаем токен для пользователя
    token = storage.insert_token(str(uuid.uuid4()), int(datetime.datetime.now().timestamp() + 3600))

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Административная панель",
                    url=str(settings.webhook_url).rstrip("/") + "/auth?token=" + str(token.value),
                )
            ]
        ]
    )
    await message.answer("Административная панель", reply_markup=kb)
