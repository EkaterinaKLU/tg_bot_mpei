# Модуль отвечает за работу административной панели

import json
import os.path
from typing import (
    Annotated,
)

from fastui.components.display import DisplayMode
from fastui.forms import (
    fastui_form,
)
from fastui import FastUI, prebuilt_html, components as c, events as e
from fastapi import (
    APIRouter,
    HTTPException,
    Depends,
    Query,
)
from fastapi.responses import HTMLResponse, FileResponse

from handlers.dependencies import auth_api_dependence
from models import User, QuestionsFineTuningForm, UpdateSettingsForm
from storage import (
    storage,
)
from utils import gen_fine_tuning_file
from settings import settings

router = APIRouter()

title = "Admin"


# Функция которая добавляет компоненты в зависимости от страницы к базовым компонентам которые должны быть на каждой странице
def base_page(
    *components: c.AnyComponent,
) -> list[c.AnyComponent]:
    return [
        c.PageTitle(text=title),
        c.Navbar(
            title=title,
            title_event=e.GoToEvent(url="/"),
            start_links=[
                c.Link(
                    components=[c.Text(text="Пользователи")],
                    on_click=e.GoToEvent(url="/users"),
                    active="startswith:/users",
                ),
                c.Link(
                    components=[c.Text(text="Обучение модели")],
                    on_click=e.GoToEvent(url="/fine-tuning"),
                    active="startswith:/fine-tuning",
                ),
                c.Link(
                    components=[c.Text(text="Настройки")],
                    on_click=e.GoToEvent(url="/settings"),
                    active="startswith:/settings",
                ),
            ],
            end_links=[c.Link(components=[c.Text(text="Выйти")], on_click=e.GoToEvent(url="/logout"))],
        ),
        c.Page(
            components=[
                *components,
            ],
        ),
    ]


# Обработчик возвращающий базовую страницу
@router.get(
    "/api/", response_model=FastUI, response_model_exclude_none=True, dependencies=[Depends(auth_api_dependence)]
)
def index_api() -> list[c.AnyComponent]:
    return base_page()


# Функция для работы с аутентификацией
@router.get("/api/auth", response_model=FastUI, response_model_exclude_none=True)
def auth_api(token: Annotated[str | None, Query()] = None) -> list[c.AnyComponent]:
    if token is None:
        raise HTTPException(status_code=403, detail="Unauthorized")
    is_valid = storage.is_token_valid(token)
    if not is_valid:
        raise HTTPException(status_code=403, detail="Unauthorized")
    return [c.FireEvent(event=e.AuthEvent(token=token, url="/"))]


# Функция для очистки аутентификации
@router.get("/api/logout", response_model=FastUI, response_model_exclude_none=True)
def logout_api(token: str = Depends(auth_api_dependence)) -> list[c.AnyComponent]:
    storage.delete_token(token)
    return [c.FireEvent(event=e.AuthEvent(token=False, url="/"))]


# Функция для показа всех пользователей на странице
@router.get(
    "/api/users", response_model=FastUI, response_model_exclude_none=True, dependencies=[Depends(auth_api_dependence)]
)
def users_api(
    page: int = 1,
) -> list[c.AnyComponent]:
    page_size = 10
    count = storage.count_all_users()
    return base_page(
        c.Table(
            data=storage.list_all_users(),
            data_model=User,
            columns=[
                c.display.DisplayLookup(field="id", title="Идентификатор пользователя", mode=DisplayMode.plain),
                c.display.DisplayLookup(
                    field="tg_user_id", title="Идентификатор пользователя в Telegram", mode=DisplayMode.plain
                ),
                c.display.DisplayLookup(field="tg_user_city", title="Город пользователя", mode=DisplayMode.plain),
                c.display.DisplayLookup(field="tg_user_phone", title="Номер пользователя", mode=DisplayMode.plain),
                c.display.DisplayLookup(field="tg_user_email", title="Email пользователя", mode=DisplayMode.plain),
                c.display.DisplayLookup(field="tg_user_first_name", title="Имя пользователя", mode=DisplayMode.plain),
                c.display.DisplayLookup(
                    field="tg_user_last_name", title="Фамилия пользователя", mode=DisplayMode.plain
                ),
            ],
            no_data_message="Пользователей нет",
        ),
        c.Pagination(
            page=page,
            page_size=page_size,
            total=count if count > 0 else 1,  # TODO dirt hack to fix pagination
        ),
    )


# Функция для получения компонентов настроек
@router.get(
    "/api/settings",
    response_model=FastUI,
    response_model_exclude_none=True,
    dependencies=[Depends(auth_api_dependence)],
)
def settings_api() -> list[c.AnyComponent]:
    return base_page(
        c.ModelForm(
            submit_url="/api/settings",
            model=UpdateSettingsForm,
            initial={"yandex_model_uri": settings.yandex_model_uri, "temperature_model": settings.temperature_model},
        )
    )


# Функция для сохранения настроек
@router.post(
    "/api/settings",
    response_model=FastUI,
    response_model_exclude_none=True,
    dependencies=[Depends(auth_api_dependence)],
)
def settings_update_api(
    form: Annotated[
        UpdateSettingsForm,
        fastui_form(UpdateSettingsForm),
    ]
) -> list[c.AnyComponent]:
    settings.yandex_model_uri = form.yandex_model_uri
    settings.temperature_model = float(form.temperature_model)
    settings.dump_to_self_file()
    return [c.FireEvent(event=e.GoToEvent(url="/settings"))]


# Функция для получения компонентов страницы с обучением модели
@router.get(
    "/api/fine-tuning",
    response_model=FastUI,
    response_model_exclude_none=True,
    dependencies=[Depends(auth_api_dependence)],
)
def fine_tuning_api() -> list[c.AnyComponent]:
    initial = {}
    if os.path.exists(settings.fine_tuning_saved_form_data_file):
        with open(settings.fine_tuning_saved_form_data_file, "r") as f:
            initial = json.load(f)
    return base_page(
        c.ModelForm(model=QuestionsFineTuningForm, display_mode="page", submit_url="/api/fine-tuning", initial=initial)
    )


# Функция для сохранения и генерации файла для обучения модели
@router.post("/api/fine-tuning", dependencies=[Depends(auth_api_dependence)])
def fine_tuning_gen_file(
    form: Annotated[
        QuestionsFineTuningForm,
        fastui_form(QuestionsFineTuningForm),
    ]
) -> list[c.AnyComponent]:
    file = gen_fine_tuning_file(form)
    with open(settings.fine_tuning_saved_form_data_file, "w") as f:
        f.write(form.model_dump_json())
    return [c.FireEvent(event=e.GoToEvent(url=f"/api/download-file?file_id={file.id}", target="_blank"))]


# Функция для скачивания файла
@router.get("/api/download-file")
def download_file(file_id: int) -> FileResponse:
    file = storage.get_file_by_id(file_id)
    if file is None:
        raise HTTPException(status_code=404, detail="File not exists or not valid")
    return FileResponse(path=file.path_to_file, media_type=file.file_mime_type, filename=file.file_name)


# Функция для UI админки
@router.get("/{path:path}")
def index() -> HTMLResponse:
    return HTMLResponse(prebuilt_html(title=title))


# TODO add deleting file after some time
# TODO add to diplom info about how to givve access to model for service account
# TODO normalizing url (/api -> /api/)
