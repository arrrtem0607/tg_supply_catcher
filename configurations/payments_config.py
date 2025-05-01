# configurations/payments_config.py

from configurations.reading_env import env


class PaymentsConfig:
    def __init__(self):
        self.__jwt_token = env("TOCHKA_JWT_TOKEN")
        self.__client_id = env("TOCHKA_CLIENT_ID")
        self.__customer_code = env("TOCHKA_CUSTOMER_CODE")
        self.__merchant_id = env("TOCHKA_MERCHANT_ID")

    def get_jwt_token(self) -> str:
        return self.__jwt_token

    def get_client_id(self) -> str:
        return self.__client_id

    def get_customer_code(self) -> str:
        return self.__customer_code

    def get_merchant_id(self) -> str:
        return self.__merchant_id

    def get_consumer_id(self) -> str:
        # по умолчанию можно использовать client_id как consumer_id
        return self.__client_id
