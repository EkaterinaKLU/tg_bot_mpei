# Файл, отвечает за объявление мидлварь, которые в дальнейшем будут задействованы в нашем коде

from typing import Any, Callable, Awaitable, Dict

from aiogram import (
    BaseMiddleware,
)
from aiogram.types import Update, TelegramObject
from aiogram.fsm.context import (
    FSMContext,
)

import exceptions
from handlers.bot.bot import (
    UserState,
)
from storage import (
    storage,
)


# Мидлваря, которая нужна для получения пользователя, когда приходит обновление от телеграм
class UserMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ):
        # Массив который хранит в себе состояние пользователя при его регистрации
        register_user_states = [
            UserState.choose_city_state,
            UserState.type_phone_state,
            UserState.type_email_state,
            UserState.type_first_name_state,
            UserState.type_last_name_state,
        ]
        # Объект для работы с состоянием пользователя
        state: FSMContext = data["state"]
        # Текущий пользователь в нашей системе который получен исходя из его tg user id
        user = storage.get_user_for_tg_user_id(
            event.callback_query.from_user.id if event.callback_query is not None else event.message.from_user.id
        )
        data["user"] = user
        # Проверка что пользователь находится в состоянии регистрации
        if event.message is not None and (
            event.message.text == "/start" or await state.get_state() in register_user_states
        ):
            return await handler(
                event,
                data,
            )
        # Кидаем исключение если пользователь не был найден
        if data["user"] is None:
            raise exceptions.TGUserNotFoundException()
        return await handler(
            event,
            data,
        )
