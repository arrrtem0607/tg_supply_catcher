from configurations.reading_env import env


class DatabaseConfig:
    def __init__(self):
        self.__db_name = env("POSTGRES_DB")
        self.__db_host = env("POSTGRES_HOST")
        self.__db_port = env.int("POSTGRES_PORT")
        self.__db_user = env("POSTGRES_USER")
        self.__db_password = env("POSTGRES_PASSWORD")
        self.__db_backup_file = env("DB_BACKUP")
        self.__db_backup_contents = env("DB_BACKUP_CONTENTS")

    def get_db_name(self) -> str:
        return self.__db_name

    def get_db_host(self) -> str:
        return self.__db_host

    def get_db_port(self) -> int:
        return self.__db_port

    def get_db_password(self) -> str:
        return self.__db_password

    def get_db_user(self) -> str:
        return self.__db_user

    def get_db_backup_file(self) -> str:
        return self.__db_backup_file

    def get_db_backup_contents(self) -> str:
        return self.__db_backup_contents

    def get_database_url(self) -> str:
        return (f"postgresql+asyncpg://{self.__db_user}:{self.__db_password}"
                f"@{self.__db_host}:{self.__db_port}/{self.__db_name}")
