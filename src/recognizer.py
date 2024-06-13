# Модуль для работы с разпознованием голоса

from typing import Literal

import httpx

from settings import settings


# Класс для работы с разпознованием голоса
class Recognizer:
    def __init__(self):
        self.yc_uri = "https://stt.api.cloud.yandex.net/speech/v1/stt:recognize"

    # Метод для распознования голоса
    async def recognize(self, file_path: str, format_audio: Literal["lpcm", "oggopus"]) -> str:
        async with httpx.AsyncClient() as client:
            with open(file_path, "rb") as file:
                r = await client.post(
                    self.yc_uri,
                    headers={"Authorization": f"Bearer {settings.token}"},
                    params={
                        # Указываем язык
                        "lang": "ru-RU",
                        # Указываем готовую yandex модель для распознования голоса
                        "topic": "general",
                        # Указываем что не надо фильтровать мат из голоса
                        "profanityFilter": False,
                        # Указываем что числа идут как обычный текст
                        "rawResults": False,
                        # Указываем формат аудио
                        "format": format_audio,
                        # Указываем id yandex cloud папки
                        "folderid": settings.folder_id,
                    },
                    # Считываем байты голоса и отправляем на сервер yandex
                    content=file.read(),
                )
                # Выкидываем исключения если ответ неуспешен
                r.raise_for_status()
                # Получаем текст из разшифрованного голоса
                return r.json()["result"]


recognizer = Recognizer()
