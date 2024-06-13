# Модуль для работы с настройками приложения

import asyncio
import json
import os
import pathlib
import time
from typing import (
    Self,
    Annotated,
    Optional,
)

import httpx
import jwt
import yaml
from pydantic import (
    BaseModel,
    UrlConstraints,
    DirectoryPath,
    computed_field,
)
from pydantic_core import (
    Url,
)
from loguru import (
    logger,
)


# Класс настроек
class Settings(
    BaseModel,
    extra="forbid",
    validate_assignment=True,
):
    # Токен тг бота
    bot_token: str
    # URL вебхука для телеграмм
    webhook_url: Annotated[
        Url,
        UrlConstraints(
            max_length=2083,
            allowed_schemes=["https"],
        ),
    ]
    # URI модели в yandex cloud
    yandex_model_uri: str
    # Yandex Cloud token
    token: Optional[str] = None
    # ID папки в yandex cloud
    folder_id: str
    # Путь до файла с приватным и публичным ключом для генерации токена для работы с yandex cloud
    key_json_file: pathlib.Path
    # Путь до sqlite3 файла
    db_path: pathlib.Path = pathlib.Path("db.db")
    # Путь до файла где хранятся последние сохранившиеся данные для генерации файла для обучение
    fine_tuning_saved_form_data_file: pathlib.Path
    # Путь до папки где будут храниться сгенерировшиеся файлы
    files_dir_path: DirectoryPath
    # Путь до файла где хранятся настройки
    self_path: pathlib.Path
    # Список с tg id которые являются админами
    tg_user_id_admins: list[int] = []
    temperature_model: float = 0.1

    # Вычисляемое поле которое хранит путь для вебхука
    @computed_field
    @property
    def webhook_path(
        self,
    ) -> str:
        return f"/{self.bot_token}"

    # Метод для цикличного обновления yandex cloud token
    async def loop_update_yc_token(
        self,
    ):
        while True:
            # every 1 minute
            await asyncio.sleep(60)
            logger.debug("Updating yc token")
            r = await self.single_update_yc_token()
            if r:
                logger.warning(f"Unsuccessful response while trying to update iam token: {r.text}")
                continue
            logger.debug("Successful update yc token")

    # Метод для одиночного обновления yandex cloud token
    async def single_update_yc_token(
        self,
    ) -> Optional[httpx.Response]:
        # If response is not None then we think that unsuccessfully updated
        with open(
            self.key_json_file,
            "r",
        ) as key:
            key = json.load(key)  # Чтение ключа из файла.
        now = int(time.time())
        payload = {
            "aud": "https://iam.api.cloud.yandex.net/iam/v1/tokens",
            "iss": key["service_account_id"],
            "iat": now,
            "exp": now + 360,
        }

        # Формирование JWT.
        encoded_token = jwt.encode(
            payload,
            key["private_key"],
            algorithm="PS256",
            headers={"kid": key["id"]},
        )
        async with httpx.AsyncClient() as client:
            r = await client.post(
                "https://iam.api.cloud.yandex.net/iam/v1/tokens",
                json={"jwt": encoded_token},
            )
            if not r.is_success:
                return r
            self.token = r.json()["iamToken"]
        return None

    # Метод для загрузки настроек из yaml файла
    @classmethod
    def from_yaml(
        cls,
        path,
    ) -> Self:
        with open(path) as f:
            cfg = yaml.safe_load(f.read())

        return cls(**cfg, self_path=path)

    # Сохранить текущее состояние настроек в свой же файл
    def dump_to_self_file(self):
        # Does not save дата начала приемной комиссии
        with open(self.self_path, "w") as f:
            d = json.loads(self.model_dump_json(exclude={"self_path", "webhook_path", "token"}))
            yaml.safe_dump(d, f)


# Получаем переменную окружения которое хранит путь до конфига
cfg_path = os.environ.get(
    "CONFIG_PATH",
    None,
)
# Кидаем исключения если переменная окружения пустая
if not cfg_path:
    raise ValueError("CONFIG_PATH environment variable not set")

# Инициализируем инстанс объекта настроек
settings = Settings.from_yaml(cfg_path)
# TODO checking temperature_model in config model and add multiplying by -.01 in form
