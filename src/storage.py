# Модуль отвечающий за работу с базой данных

import asyncio
import pathlib
import os
from datetime import datetime
from typing import Optional, NoReturn
import sqlite3

from loguru import logger

from models import (
    User,
    File,
    Token,
)
from settings import (
    settings,
)


# Класс для работы с базой данных
class Storage:
    def __init__(
        self,
        db_path: pathlib.Path,
    ):
        # Сохраняем путь до sqlite3 файла
        self.db_path = db_path
        # Проводим первичную инициализацию базы данных
        self.setup_database()

    # Метод для получения подключения к базе данных
    def get_conn(
        self,
    ) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    # Метод для создания нужных таблиц и индексов для работы нашего приложения
    def setup_database(
        self,
    ):
        queries = [
            "CREATE TABLE IF NOT EXISTS tg_users("
            "id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,"
            "tg_user_id INTEGER UNIQUE NOT NULL,"
            "tg_user_city TEXT NOT NULL,"
            "tg_user_phone TEXT NOT NULL,"
            "tg_user_email TEXT NOT NULL,"
            "tg_user_first_name TEXT NOT NULL,"
            "tg_user_last_name TEXT NOT NULL"
            ")",
            "CREATE TABLE IF NOT EXISTS files("
            "id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,"
            "path_to_file TEXT UNIQUE NOT NULL,"
            "file_name TEXT NOT NULL,"
            "mime_type TEXT NOT NULL,"
            "valid_until INTEGER NOT NULL"
            ")",
            "CREATE TABLE IF NOT EXISTS tokens("
            "id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,"
            "value TEXT UNIQUE NOT NULL, "
            "valid_until INTEGER NOT NULL"
            ")",
            "CREATE INDEX IF NOT EXISTS tg_user_id_tg_users_idx ON tg_users (tg_user_id)",
            "CREATE INDEX IF NOT EXISTS value_tokens_idx ON tokens (value)",
            "CREATE INDEX IF NOT EXISTS valid_until_tokens_idx ON tokens (valid_until)",
            "CREATE INDEX IF NOT EXISTS valid_until_files_idx ON files (valid_until)",
        ]
        with self.get_conn() as conn:
            cursor = conn.cursor()
            for query in queries:
                cursor.execute(query)

    # Метод для создания пользователя после его регистрации в боте
    def create_tg_user(
        self,
        tg_user_id: int,
        tg_user_city: str,
        tg_user_phone: str,
        tg_user_email: str,
        tg_user_first_name: str,
        tg_user_last_name: str,
    ) -> NoReturn:
        query = (
            "INSERT INTO "
            "tg_users(tg_user_id, tg_user_city, tg_user_phone, tg_user_email, tg_user_first_name, tg_user_last_name) "
            "VALUES (?, ?, ?, ?, ?, ?)"
        )
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                query,
                (tg_user_id, tg_user_city, tg_user_phone, tg_user_email, tg_user_first_name, tg_user_last_name),
            )

    # Метод для обновления города пользователя
    def update_tg_user_city(self, tg_user_id: int, tg_user_city: str) -> NoReturn:
        query = """
        UPDATE tg_users SET tg_user_city = ? WHERE tg_user_id = ?
        """
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (tg_user_city, tg_user_id))

    # Метод для обновления телефона пользователя
    def update_tg_user_phone(self, tg_user_id: int, tg_user_phone: str) -> NoReturn:
        query = """
        UPDATE tg_users SET tg_user_phone = ? WHERE tg_user_id = ?
        """
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (tg_user_phone, tg_user_id))

    # Метод для обновления почты пользователя
    def update_tg_user_email(self, tg_user_id: int, tg_user_email: str) -> NoReturn:
        query = """
        UPDATE tg_users SET tg_user_email = ? WHERE tg_user_id = ?
        """
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (tg_user_email, tg_user_id))

    # Метод для обновления имени пользователя
    def update_tg_user_first_name(self, tg_user_id: int, tg_user_first_name: str) -> NoReturn:
        query = """
        UPDATE tg_users SET tg_user_first_name = ? WHERE tg_user_id = ?
        """
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (tg_user_first_name, tg_user_id))

    # Метод для обновления фамилии пользователя
    def update_tg_user_last_name(self, tg_user_id: int, tg_user_last_name: str) -> NoReturn:
        query = """
        UPDATE tg_users SET tg_user_last_name = ? WHERE tg_user_id = ?
        """
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (tg_user_last_name, tg_user_id))

    # Метод для получения всего списка пользователей
    def list_all_users(
        self,
    ) -> list[User]:
        query = "SELECT id, tg_user_id, tg_user_city, tg_user_phone, tg_user_email, tg_user_first_name, tg_user_last_name FROM tg_users"
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
        return [
            User(
                id=row[0],
                tg_user_id=row[1],
                tg_user_city=row[2],
                tg_user_phone=row[3],
                tg_user_email=row[4],
                tg_user_first_name=row[5],
                tg_user_last_name=row[6],
            )
            for row in rows
        ]

    # Метод для подсчета пользователей
    def count_all_users(
        self,
    ) -> int:
        query = "SELECT count(1) FROM tg_users"
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            row = cursor.fetchone()

        return row[0]

    # Метод для получения пользователя по его tg user id
    def get_user_for_tg_user_id(
        self,
        tg_user_id: int,
    ) -> Optional[User]:
        query = "SELECT id, tg_user_id, tg_user_city, tg_user_phone, tg_user_email, tg_user_first_name, tg_user_last_name FROM tg_users WHERE tg_user_id = ?"
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                query,
                (tg_user_id,),
            )
            row = cursor.fetchone()
        if row is None:
            return None
        return User(
            id=row[0],
            tg_user_id=row[1],
            tg_user_city=row[2],
            tg_user_phone=row[3],
            tg_user_email=row[4],
            tg_user_first_name=row[5],
            tg_user_last_name=row[6],
        )

    # Метод для получения файла по его id
    def get_file_by_id(self, file_id: int) -> Optional[File]:
        query = """
        SELECT id, path_to_file, file_name, mime_type FROM files WHERE id = ? AND valid_until > ?
        """
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (file_id, int(datetime.now().timestamp())))
            row = cursor.fetchone()
        if row is None:
            return None
        return File(id=row[0], path_to_file=row[1], file_name=row[2], file_mime_type=row[3])

    # Метод для вставки новой записи о файле
    def insert_file(self, path_to_file: str, file_name: str, file_mime_type: str, valid_until: int) -> File:
        query = """
        INSERT INTO files(path_to_file, file_name, mime_type, valid_until) VALUES (?, ?, ?, ?)
        RETURNING id, path_to_file, file_name, mime_type
        """
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (path_to_file, file_name, file_mime_type, valid_until))
            row = cursor.fetchone()
        return File(id=row[0], path_to_file=row[1], file_name=row[2], file_mime_type=row[3])

    # Метод для вставки новой записи о токене
    def insert_token(self, token: str, valid_until: int) -> Token:
        query = """
        INSERT INTO tokens(value, valid_until) VALUES (?, ?)
        RETURNING id, value, valid_until
        """
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (token, valid_until))
            row = cursor.fetchone()
        return Token(id=row[0], value=row[1], valid_until=row[2])

    # Метод для удаления токена по его значению
    def delete_token(self, value: str) -> NoReturn:
        query = """
        DELETE FROM tokens WHERE value = ?
        """
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (value,))

    # Метод для удаления просроченных токенов
    def delete_expired_tokens(self) -> NoReturn:
        query = """
        DELETE FROM tokens WHERE valid_until <= ?
        """
        with self.get_conn() as conn:
            cursor = conn.cursor()
            exc_info = cursor.execute(query, (datetime.now().timestamp(),))
        logger.debug(f"Successfully deleted {exc_info.rowcount} expired tokens")

    # Метод для проверки валидности токена
    def is_token_valid(self, token: str) -> bool:
        query = """
        SELECT EXISTS(SELECT 1 FROM tokens WHERE value = ? AND valid_until > ?)
        """
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (token, int(datetime.now().timestamp())))
            row = cursor.fetchone()
        return row[0]

    # Метод который работает в фоне для удаления просроченных токенов каждую минуту
    async def loop_delete_old_tokens(self) -> NoReturn:
        while True:
            # every 1 minute
            await asyncio.sleep(60)
            logger.debug("Deleting old tokens")
            try:
                self.delete_expired_tokens()
            except Exception as e:
                logger.exception(
                    "Critical error caused while deleting old tokens",
                    e,
                )
                continue
            logger.debug("Successfully deleted old tokens")

    # Метод для удаления просроченных файлов
    def delete_expired_files(self) -> NoReturn:
        query = """
           DELETE FROM files WHERE valid_until <= ?
           RETURNING path_to_file
           """
        with self.get_conn() as conn:
            cursor = conn.cursor()
            exc_info = cursor.execute(query, (datetime.now().timestamp(),))
            files = cursor.fetchall()
        for file in files:
            os.remove(file[0])
        logger.debug(f"Successfully deleted {exc_info.rowcount} expired files")

    # Метод который работе в фоне для удаления просроченных файлов каждую минуту
    async def loop_delete_old_files(self) -> NoReturn:
        while True:
            # every 1 minute
            await asyncio.sleep(60)
            logger.debug("Deleting old files")
            try:
                self.delete_expired_files()
            except Exception as e:
                logger.exception(
                    "Critical error caused while deleting old files",
                    e,
                )
                continue
            logger.debug("Successful deleted old files")


# Инициализируем инстанс класса для работы с базой данных
storage = Storage(settings.db_path)
