# Модуль который хранит в себе различные модели используемы в нашем приложении
from enum import StrEnum
import pathlib
import uuid
from typing import Annotated
from datetime import date, datetime


from pydantic import BaseModel, Field
from pydantic.functional_validators import field_validator
from pydantic_core import PydanticCustomError


# Модель для хранения данных о пользователе
class User(
    BaseModel,
    extra="forbid",
):
    id: int
    tg_user_id: int
    tg_user_city: str
    tg_user_phone: str
    tg_user_email: str
    tg_user_first_name: str
    tg_user_last_name: str


# Модель для хранения данных о файле
class File(BaseModel, extra="forbid"):
    id: int
    path_to_file: pathlib.Path
    file_name: str
    file_mime_type: str


# Модель для хранения данных о токене
class Token(BaseModel, extra="forbid"):
    id: int
    value: uuid.UUID
    valid_until: int


# Модель для формирования и хранения данных в форме в UI админке в блоке настроек
class UpdateSettingsForm(BaseModel):
    yandex_model_uri: Annotated[str, Field(title="Путь до модели")]
    # Скорее всего в FastUI перепутаны ge и le
    temperature_model: Annotated[str, Field(title="Температура модели")]

    @field_validator("temperature_model")
    def validate_temperature_model(cls, v: str):
        try:
            v_float = float(v)
        except ValueError:
            raise PydanticCustomError("invalid_value", "Cant parse temperature_model to float")
        if not (0 <= v_float <= 1):
            raise PydanticCustomError("invalid_value", "temperature_model must be 0 <= v <= 1")
        return v


# Enum для хранения возможных значений формы встречи
class FodEnum(StrEnum):
    face_to_face = "очная встреча"
    distance = "дистанционная встреча"


# Модель для формирования и хранения данных в форме в UI админке в блоке генерации файла
class QuestionsFineTuningForm(
    BaseModel,
    extra="forbid",
):
    ac_date_start: Annotated[date, Field(title="Дата начала приемной комиссии")]
    ac_date_end: Annotated[date, Field(title="Дата конца приемной комиссии")]
    od_date: Annotated[datetime, Field(title="Даты Дней открытых дверей")]
    od_address: Annotated[str, Field(title="Адрес проведения Дня открытых дверей")]
    fod: Annotated[FodEnum, Field(title="Формат проведения Дня открытых дверей")]
    doc_esys_date_start: Annotated[date, Field(title="Дата начала приема документов в электронном формате")]
    doc_ftf_date_start: Annotated[date, Field(title="Дата начала приема документов в очном формате")]
