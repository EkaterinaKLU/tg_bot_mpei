# Модуль для инициализации бота

from typing import NoReturn

from aiogram import (
    Dispatcher,
    Bot,
)
from aiogram.enums import (
    ParseMode,
)
from aiogram.filters import (
    ExceptionTypeFilter,
)
from aiogram.types import (
    ErrorEvent,
    BotCommand,
)
from aiogram.fsm.storage.memory import (
    MemoryStorage,
)
from loguru import (
    logger,
)

from exceptions import (
    TGUserNotFoundException,
)
from middlewares import (
    UserMiddleware,
)
from handlers.bot.bot import (
    router,
)

from settings import (
    settings,
)

# Dispatcher - это рутовый роутер для направленмия обновления в соответствующий хендлер
dp = Dispatcher(storage=MemoryStorage())
# Добавляем мидлварю для работы с пользователями
dp.update.middleware(UserMiddleware())

# Добавляем роутер в наш рутовый роутер
dp.include_router(router)

# Инициализируем нашего бота
bot = Bot(
    token=settings.bot_token,
    parse_mode=ParseMode.HTML,
)


# Функция для установления вебхука на стороне телеграм
async def set_webhook(
    bot: Bot,
) -> NoReturn:
    try:
        # Удаляем старый вебхук
        await bot.delete_webhook(drop_pending_updates=True)
        # Устанавливаем новый вебхук
        await bot.set_webhook(
            f"{str(settings.webhook_url).rstrip('/')}{settings.webhook_path}",
            drop_pending_updates=True,
            max_connections=100,
        )
    except Exception as e:
        logger.error(f"Can't set webhook - {e}")
        raise


# Функция для установления меню с командами в интерфейсе телеграм
async def set_bot_commands_menu(
    bot: Bot,
) -> NoReturn:
    commands = [
        BotCommand(
            command="/ask",
            description="Задать вопрос помощнику абитуриента",
        ),
        BotCommand(
            command="/start",
            description="Начать работу с ботом или показать главное меню",
        ),
        BotCommand(command="/settings", description="Настройки пользователя"),
    ]
    try:
        await bot.set_my_commands(commands)
    except Exception as e:
        logger.error(f"Can't set commands - {e}")


# Стартуем телеграм бота
async def start_telegram():
    await set_webhook(bot)
    await set_bot_commands_menu(bot)


# Обработчик исключения TGUserNotFoundException
@dp.error(ExceptionTypeFilter(TGUserNotFoundException))
async def tg_user_not_found_exception_handler(
    event: ErrorEvent,
):
    message = event.update.message
    if event.update.callback_query is not None:
        await event.update.callback_query.answer()
        message = event.update.callback_query.message
    await message.answer("Такое ощущение, что вы не зарегистрированы в нашей системе. Пожалуйста, введите /start")


# Обработка любых других исключений
@dp.error()
async def error_handler(
    event: ErrorEvent,
):
    logger.exception(
        "Critical error caused",
        event.exception,
    )
    message = event.update.message
    if event.update.callback_query is not None:
        await event.update.callback_query.answer()
        message = event.update.callback_query.message
    await message.answer("Произошла непредвиденная ошибка")
