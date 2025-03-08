from configurations.reading_env import env


class BotConfig:
    def __init__(self):
        self.__token = env("TOKEN")
        self.__developers_id = env.list("DEVELOPER_IDS")

    def get_token(self) -> str:
        return self.__token

    def get_yandex_disk_token(self) -> str:
        return self.__yandex_disk_token

    def get_developers_id(self) -> list[int]:
        return self.__developers_id
