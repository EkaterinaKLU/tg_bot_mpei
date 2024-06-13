# Входная точка для нашего приложения
import asyncio
from contextlib import (
    asynccontextmanager,
)

from fastapi import FastAPI

from bot import (
    start_telegram,
    dp,
    bot,
)
from settings import (
    settings,
)
from handlers.admin import (
    router as admin_router,
)
from storage import storage


# Функция для жизненного цикла веб сервера
@asynccontextmanager
async def lifespan(
    _: FastAPI,
):
    # Стартуем телеграмм
    await start_telegram()

    # Единично обновляем yandex cloud token
    response = await settings.single_update_yc_token()
    if response:
        raise RuntimeError("Cant set yc_token, error: {}".format(response.text))
    # Запускаем задачу на обновление yandex cloud token
    asyncio.create_task(settings.loop_update_yc_token())
    # Запускаем задачу на удаление старых токенов
    asyncio.create_task(storage.loop_delete_old_tokens())
    # Запускаем задачу на удаление старых файлов
    asyncio.create_task(storage.loop_delete_old_files())
    yield


# Инициализируем инстанс нашего сервера
app = FastAPI(
    lifespan=lifespan,
    openapi_url=None,
)
# Добавлеям роутер ответственный за админские пути
app.include_router(admin_router)


# Добавляем обработчик нашего вебхука
@app.post(settings.webhook_path)
async def tg_webhook(
    update: dict,
):
    await dp.feed_webhook_update(
        bot=bot,
        update=update,
    )
