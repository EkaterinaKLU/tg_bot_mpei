# Модуль для работы с LLM yandex cloud
import httpx

from settings import (
    settings,
)


class LLM:
    def __init__(
        self,
    ):
        self.yc_uri = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

    # Метод для того чтобы спросить вопрос у LLM
    async def ask(
        self,
        question: str,
    ) -> str:
        d = {
            # URI модели yandex cloud
            "modelUri": settings.yandex_model_uri,
            "completionOptions": {
                # Указываем что нам надо сразу получить ответ
                "stream": False,
                # Указываем температуру ответа
                "temperature": settings.temperature_model,
                # Указываем максимальное количество токенов
                "maxTokens": "2000",
            },
            # Указываем вопрос
            "messages": [
                {
                    "role": "user",
                    "text": question,
                }
            ],
        }
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(
                self.yc_uri,
                json=d,
                headers={
                    # Указываем в хедерах токен
                    "Authorization": f"Bearer {settings.token}",
                    # Указываем yandex cloud папку
                    "x-folder-id": settings.folder_id,
                },
            )
            r.raise_for_status()
            # Достаем ответ
            return r.json()["result"]["alternatives"][0]["message"]["text"]


llm = LLM()
