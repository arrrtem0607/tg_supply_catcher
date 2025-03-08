from configurations.db_config import DatabaseConfig
from configurations.bot_config import BotConfig
# from configurations.sheets_config import SheetsConfig


class MainConfig():
    db_config: DatabaseConfig = DatabaseConfig()
    bot_config: BotConfig = BotConfig()
    # sheets_config: SheetsConfig = SheetsConfig()


def get_config() -> MainConfig:
    return MainConfig()
