import logging
import random
import functools
import asyncio
import aiohttp
import subprocess
import json
import requests
from aiohttp import ClientResponseError, ClientSession

from datetime import datetime, timedelta
from configurations.reading_env import Env

logger = logging.getLogger(__name__)

def use_proxy(func):
    @functools.wraps(func)
    async def wrapper(self, *args, **kwargs):
        if self.proxy_manager:
            proxy_url = await self.proxy_manager.get_proxy()
            logger.info(f"Используется прокси: {proxy_url}")
            try:
                return await func(self, *args, **kwargs, proxy_url=proxy_url)
            finally:
                await self.proxy_manager.release_proxy(proxy_url)
        else:
            return await func(self, *args, **kwargs)

    return wrapper

class WildberriesAPI:
    def __init__(self, proxy_manager=None, phone_number=None, cookie_string=None):
        self.proxy_manager = proxy_manager
        self.json_rpc_number = 1
        self.phone_number = phone_number
        self.sticker = None
        self.cookie_string = cookie_string
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
            "accept": "*/*",
            "content-type": "application/json",
            "app-name": "seller.seller-auth",
            "wb-apptype": "web",
            "wb-appversion": "v1.51.0",
            "origin": "https://seller-auth.wildberries.ru",
            "referer": "https://seller-auth.wildberries.ru/ru/?redirect_url=https%3A%2F%2Fseller.wildberries.ru%2F",
            "locale": "ru",
        })
        if cookie_string:
            self.session.cookies.update(self.parse_cookies(cookie_string))

    @staticmethod
    def _initialize_headers(cookie_string: str):
        """
        Инициализирует и возвращает заголовки для HTTP-запросов.

        Args:
            cookie_string (str): Строка с куками.

        Returns:
            dict: Заголовки запроса.
        """
        headers = {
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "ru,en;q=0.9",
            "content-type": "application/json",
            "origin": "https://seller.wildberries.ru",
            "referer": "https://seller.wildberries.ru/",
            "user-agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/128.0.0.0 YaBrowser/24.10.0.0 Safari/537.36"
            ),
            "cookie": cookie_string,
        }
        return headers

    def get_unique_id(self):
        """
        Генерирует уникальный идентификатор для JSON-RPC запроса.

        Returns:
            str: Уникальный идентификатор.
        """
        unique_id = f"json-rpc_{self.json_rpc_number}"
        self.json_rpc_number += 1
        return unique_id

    @use_proxy
    async def _post(self, url: str, json: dict, headers: dict, session: ClientSession, proxy_url=None):
        """
        Вспомогательный метод для отправки POST-запроса.

        Args:
            url (str): URL-адрес.
            json (dict): Тело запроса в формате JSON.
            headers (dict): Заголовки запроса.
            session (ClientSession): Сессия для выполнения запросов.
            proxy_url (str, optional): URL прокси, если proxy_manager активен.

        Returns:
            dict: Ответ сервера в формате JSON.

        Raises:
            Exception: В случае ошибки запроса.
        """
        try:
            async with session.post(
                url, json=json, headers=headers, proxy=proxy_url
            ) as response:
                response.raise_for_status()
                return await response.json()
        except Exception as e:
            logger.error(f"Ошибка POST-запроса: {e}")
            raise

    @staticmethod
    def parse_cookies(cookie_str):
        cookies = {}
        for item in cookie_str.split(";"):
            if "=" in item:
                key, value = item.strip().split("=", 1)
                cookies[key] = value
        return cookies


    @staticmethod
    def get_secure_token():
        try:
            """Fetch and solve captcha, returning the token."""
            token_url = "https://antibot.wildberries.ru/api/v1/create-one-time-token"

            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
                "Accept": "*/*",
                "Accept-Encoding": "gzip, deflate, br, zstd",
                "Accept-Language": "ru,en;q=0.9",
                "Origin": "https://seller-auth.wildberries.ru",
                "Referer": "https://seller-auth.wildberries.ru/",
                "Content-Type": "application/json",
                "X-WB-Antibot-Key": "217cc4d5276448d6a980d07034a3c89c",
                "X-WB-Antibot-SDK-Version": "1.0.0",
            }
            r = requests.post(token_url, headers=headers, json={
                "action": "auth",
                "challenge": {},
                "userScope": {}
            })
            print(f"🔐 1️⃣ Token попытка #1 — статус: {r.status_code}")
            print(f"{r.text}")
            try:
                resp = r.json()
            except json.JSONDecodeError:
                print("❌ Невалидный JSON:\n", r.text)
                return None

            if resp.get("code") == 498 and "challenge" in resp:
                payload = resp["challenge"].get("payload")
                if not payload:
                    print("❌ Payload отсутствует в challenge!")
                    return None

                print("⚠️ Challenge required — пробуем повторно с payload")

                # Повторный запрос с payload
                response = requests.post(token_url, headers=headers, json={
                    "challenge": {
                        "scriptPath": "/scripts/challenge_fingerprint_v1.0.3.js",
                        "payload": payload
                    },
                    "solution": {
                        "payload": "bNGEsMWEsMTcsMTAsMywxNiw3NCw2LDQ4LGYsMTYsNDAsNWIsZiw1OSxhLDE5LGMsNDEsNTQsNTUsMWQsNTMsMywzLDEwLDFjLDRmLDU4LDVjLDUyLGUsNDUsMTcsMTAsNWQsNDUsMTgsNTMsNTMsNDgsNTQsZSw0MSw1YSw4LGMsNTQsNTUsMTYsMTQsMWQsNTUsNTEsNCwxOCw1NSw0MiwxNiw0MSw1Niw0Nyw1MSw1YSw1YSw1Yiw0Miw0ZSw3LDU3LDcsMWQsMixlLDQyLDRiLGQsYyw0MSxjLDQxLDRkLDQyLGUsOCw0Niw1MSw0NSw0LDAsNGUsNTMsNWIsMWIsNDYsNGUsNWIsNDIsNWIsNTUsNTQsMWQsNyw1MiwwLDRhLDAsMWQsMSwxNiw1Miw0MywxZiw1LDU3LDEzLDQyLDE2LDExLDcsMTMsMiw2LDUwLDRkLDU3LDMsOCwxYSwyLDQ2LDVlLDUyLDU2LDU1LDRhLDU4LDFkLDMsNTIsNSw0YSwzLDUsMTMsMTQsNDAsMiwxNiwxNCw2Myw0LDVmLDEyLGIsZCxmLGYsZSw0Nyw1Niw0YiwxZCwxOCwxYyw0NSxmLDQzLDU3LDVmLDQzLDRiLDExLDVjLDQyLDQxLDMsNTQsMWUsMyxhLDE4LDE1LGEsOCw1MiwxLDVhLGQsMTksNTQsNTYsNDgsZCw1NSwxNSwxMyw5LDQ4LDRmLDUxLDUwLGQsNDQsNDcsMWYsMSxiLDYsMWMsNSw1NywxMiw0Yyw1Yiw1Yiw0NSw1NSxlLDRmLDQ2LDgsNWMsYSw0OCw0MSw1LDcsMiw0Niw1Yiw0Yyw0Myw2LDQ1LDRhLDViLDVmLDMsMiwyLDMsNiwxNiwxLDFjLDYsNGYsMiw0NCw0OSw1Miw1Myw0YSxkLDE0LDE1LDEsNDcsNGUsMWYsNTQsNGMsNTAsNGYsMWQsMWEsNTUsNDMsMTYsNGMsNWUsNTUsNDAsZiwyLDYsMywzLDE2LDIsNCwxNCw0ZCwxMCw4LDUxLDVkLDU2LDRkLDMsNCwzLDE3LDE3LDViLDU2LDQzLGYsMyw4LDQzLDE2LDVmLDQxLDE3LDU4LDFhLDE4LDEwLDE2LDVmLDU2LDU2LDUxLDRhLDQzLDU3LDUyLDQzLDgsM2YsMTIsNDEsNDQsMWEsNGUsNDEsMyxhLDE3LDNjLDEsNDMsNiwzLDE1LDQ4LDYwLGMsZSwwLDdkLDRhLDUxLDU0LDAsNDgsNDEsNTUsNTAsMWEsYiwxMCw0NCwxNCwxMCwxOSwxYywxMSw1Yyw1MSxmLDYsMzIsMWQsNDUsNCw1ZSw0Myw1OCwxOSw0Myw0MCw1ZCw4LDYsMzEsNTQsNDgsNTEsNDEsNDQsMTcsNjgsMTIsNjQsNTcsNDMsNDYsNTcsMyw1ZSwxLDEwLDc3LDVlLDViLDE3LGUsMyxhLDQxLDQxLDZiLGUsMTAsZiwwLDU5LGUsNWYsMiwxNSw1ZCw1NCw1ZCw1MSw3LDU5LDVhLDVmLDVhLDE3LDQxLDU2LDUwLDQzLDFlLDQ2LDYwLDVjLDQzLDRjLDMsMSxhLDEsMTUsMjUsNDIsMiwxNyxmLDQsNDMsNDAsNDUsMjUsYSw1Ziw1NSw1NSw0Niw1YywxNyw0Nyw1NSw0Yyw0YywxZSw0Miw1Miw3LDEwLDM5LDFjLDExLDU4LDRiLDMyLDExLDksMTAsNWEsMTUsNTQsMTEsNywxMSwyMiw0Miw1YSwxNixhLDE2LDU5LDVkLDVhLDQ2LDQ0LDE3LDQ3LDQyLDQxLDVkLDRjLDFlLDE0LDQsNDQsNSw1Yyw3Ziw1NCw1Niw1LDE3LGUsNDYsZiw1MiwxZSw0ZCw0MCwxMixkLDU4LDUzLGMsZCwxNixmLDIsNGYsMTAsMTYsNDEsNDYsNTcsNWQsNTYsNDIsMTAsYywzYSwxMCwzNCw3NCw3NSwxMSw2ZSxiLDYsMTEsMSw0Nyw0MywxLDQzLDIxLGEsMTMsNDIsNTksMCw0MywzNSw2OSw3ZSwxNCw2NCxmLDQ4LDQ0LDU1LDQ2LDFhLDFkLDEwLDc1LDksNDAsYiw1ZCw1YSw0NCw1NSw0MiwzMywyMiwyMiwxNSwzNyw0NCw0LDE1LDcsMTMsZiwxOCw0NywyZSxjLDRlLDRhLDViLDQxLDksNGIsNDcsMTAsNzEsNWMsNTYsNTcsMTYsMzEsNzYsMjIsMTAsNjUsNTgsNWQsMTUsNiwxNCw0NiwxOSw0Myw3YSw0LDAsMjksOCw1OSwxNCw3LDE2LGMsNDEsNGMsMTksNWIsOCxkLDYzLDc0LDcyLDFhLDZjLDFlLDE0LDExLDVlLDExLDU3LDVhLDVmLDRiLDM2LDExLDEzLDEsN2MsZiw1ZSwxNSwzLGMsMiw0OCwxNiw1ZiwxNywxNyw1OCw1ZCw0OSwxZSw0NCw0OSw1Yyw1Myw0MSw1NSw1NCw1Yyw0MiwyNCw1ZSwxLDVkLDU2LDVmLDRjLDIzLDE3LDEyLDE2LDQ2LDQzLDE3LDNhLDQwLGUsMCw0Myw1Myw0Nyw0Ziw0Nyw0MCw2Nyw1ZCw1YyxmLDU5LDExLDZkLDE4LDFhLDU0LDQwLDQ0LGUsNDAsMzAsNDIsNTIsNTIsNWQsNDAsNTksNDQsMzAsNGMsMTEsNDgsMjQsMTAsMTAsZSw1ZixlLDQ1LDIwLDQsNDMsNTYsNWIsNDYsNDYsNWYsNTYsNTEsNTAsMTgsNDEsNDAsNTksMTEsNTcsMTYsNDQsNWEsNTQsNGIsNDIsYywwLDQ0LDViLDE0LDQxLGQsNDIsNGEsMTMsNDgsNTUsMSxhLGIsNGEsMTgsMTMsMiw0MSw0LDZmLDVlLDE0LDE4LDExLDEyLDU3LDE1LDEyLGMsNDQsNDcsNDEsNGIsNTgsNGMsNDksNSw1YiwxNSw0NCwzLGQsMTYsNGYsNWEsNWQsOSw3LDcsNDgsNGEsNDYsNWIsMyw1ZSwxZCw0Miw0MSwxNyw0Miw1MSw0NCw4LDQyLDEwLDQzLDFjLDUyLDUwLDMsZixhLDEsNWIsNiw0OCwzZSw0LGIsZiw0YSw1MSwxNywxMywxNyw0NCw1Niw0MCw2ZCwxMCwxYywxZCwwLDFhLGIsMWYsNTgsNDUsNWIsNyw1NSxhLDcsNyxiLDViLDNmLDgsNDQsMTUsNDEsZCwwLDE2LDQyLDEzLGQsMWMsZCwxNywxMSw1ZCw0YixlLDFkLDQ5LDRjLDVkLDQ0LDVkLDVhLDVlLDQ2LDE4LDE2LDViLDgsNTQsNTEsNTQsNGEsMTAsYSwzLDE3LDFiLDEzLDU4LDRlLDExLDEsMTMsNDQsNDQsMTEsMTAsNGEsNGUsNTAsNTUsNWUsYSw0OCw1ZCw1Nyw1MSw2Nyw1Nyw1Yiw1OCw2LDU3LDE2LDQwLDQxLDU4LDU2LDE2LDNjLDEwLDU1LDFiLDUxLDMsNTIsNGMsOCwxMiwxNywxLDU0LDU5LDUxLDFlLDksMSxiLDRmLDcxLDVkLDEwLDE0LDE4LDExLDUzLDQyLDQxLDVhLDEwLDQ0LDQzLDQyLDIsNGQsNGMsNyxhLDQxLDgsNGYsZSwxNiw0YywxNiw0NCw1OCwxLDEsMCw1Ziw0YSw1ZCw1NywxNSwzLDQxLDQ1LDFiLDRiLDUyLDQwLDVmLDExLDQ2LDE3LDFmLDUwLDU5LDU5LGUsZiwzLGEsNTIsNCw3Miw3LGIsYyw2LDQ4LDQ2LDE1LDExLGMsNDMsNGMsNmIsNDQsNTcsMywzLDFlLDcsMTYsNWIsNDEsYyw1NCwzLDVlLDQsMCwyLGIsNTMsM2YsOCw0NCwxNSw0MSxkLDAsMTYsNDIsMjAsNWYsNDYsNCwxYSw0Yiw0MCw1OSw0NCwxMiw0ZSwxMSw1Miw1ZSw1Yiw1Niw0OCw1Ziw1OSwxNCw0MSw1YSwxOSw2Ziw1ZiwxOCw0Miw0Myw0Niw1LDQxLDQxLDU1LDQsNGMsMSxlLDQxLDU4LDAsMCwxMSxkLDEwLDVjLDQ2LDEyLDVkLDQwLGEsMWIsMTcsNTAsNWMsNDIsOCw1MCxiLDQ0LDFkLDQ2LDUxLGUsNyw0LDEsNDcsMTMsNDQsNCwxMSw0YywxMyw1OCwxYiwxNiwwLDE3LDQ0LDQ4LDQwLDQxLDQ5LDRlLDViLDUxLDU4LDU0LDU0LDVjLDUxLDQsNmQsMiw1OSw1ZCw1Niw1ZCwxMCwxMywxNCxkLDViLDE1LDcyLDE3LDUzLDRjLDUxLDMsNyw0Yiw5LDE2LDE3LGQsNSw4LDUyLDFlLDEsNywzLDExLDZkLDVjLDE2LDQxLDEyLDQ0LDUxLDQ3LDExLDQwLDcsNGQsMSwxLDQxLDI1LDRjLDE1LDMsNDIsNDksNDUsNDAsMTEsMTMsMTYsMTcsMTcsMWIsNTMsOCw1OSw1YSw1Miw1Yiw0YywxZiw0NSw1ZixkLDU2LDYsNTUsNDEsNDMsNTEsNywxMCw0OCwxNiw0MCw0ZSw1ZSwyLDEwLGIsMTEsNTksNDcsNGEsMCxkLDRjLDU0LDU4LDU3LDgsNGEsNTYsNmYsNTIsNTEsNWYsNTUsNTMsMTMsNDIsMTYsNTksNWQsNDUsNjcsMTQsNTIsNDgsNTQsMWIsNTIsMyxiLDExLDU4LDU0LDFjLGUsNTEsNTEsNWQsMWYsOSwxZCw2ZSw4LGQsMTMsMTAsMTQsNTksNDUsMTIsN2EsNDEsMWEsYyw0NCw0Nyw0MSw0Yiw1OCw0Yyw0OSwxNyw0MSwwLDU5LDgsMSw0ZiwzLDRjLDQ3LGUsNiwxMSwwLDgsNiwxYywxMSw0Ziw1MSw1MSw0Nyw1Myw1NCw0NiwxOCwxMyw0Nyw0Yiw0Niw1Yyw1ZCxhLDUyLDRjLDE1LDEsNTksZCw0OCwxMyw0ZiwzLDE0LDU5LDVjLDQ4LDUsMTcsNDIsNTYsNDAsMWQsMTAsMWMsMWQsNSwwLDE2LDEsMWQsNDUsMTUsNTMsMTAsNTksNTAsMWUsNTIsMTEsNGMsNWYsNTYsMCw0ZiwxZSw1LDU1LDcsNTYsNDksYywwLDRkLDYsNDUsNGQsNWEsNTksNDgsNDcsNDAsYSw2LDIsMCwzLGUsNTQsNiw1MywwLDFhLDZkLDU2LDQyLDQzLDQ2LDQ0LDU0LDE1LGQsMCwxMSwxYixmLDRlLDE0LGUsNGQsMTYsNDIsNTQsNDIsNTcsMjUsNDUsNTIsNWMsNTgsNWQsNWYsNTUsNTMsNDEsMWEsYyw0NCw0Nyw0MSw0Yiw1OCw0Yyw0OSwxNyw0MSwwLDU5LDgsMSw0ZiwzLDRjLDQ3LGUsNiwxMSwwLDgsNiwxYywxMSw0Ziw1MSw1MSw0Nyw1Myw1NCw0NiwxOCwxMyw0Nyw0Yiw0Niw1Yyw1ZCxhLDUyLDRjLDE1LDEsNTksZCw0OCwxMyw0ZiwzLDE0LDU5LDVjLDQ4LDUsMTcsNDIsNTYsNDAsMWQsMTAsMWMsMWQsNSwwLDE2LDEsMWQsNDUsMTUsNTMsMTAsNTksNTAsMWUsNTIsMTEsNGMsNWYsNTYsMCw0ZiwxZSw1LDU1LDcsNTYsNDksYywwLDRkLDYsNDUsNGQsNWEsNTksNDgsNDcsNDAsYSw2LDIsMCwzLGUsNTYsNCw1ZCw5LDFhLDZkLDU2LDQyLDQzLDQ2LDQ0LDU0LDE1LGQsMCwxMSwxYixmLDRlLDE0LGUsNGQsNiw1Ziw1ZCw1NSw0NiwzLDYyLDVkLDU1LDYwLDUxLDVjLDU3LDYyLGUsNTksMSw1ZSwxMywxOSw1MCwxNiwxNywxNiwxNyxmLDRlLDIsMTIsMTYsMywxNSw0NCw1Nyw0OCwxLDQsNWUsNTMsNTEsNDYsNGIsMWQsMSwxZSw0Myw1YSw1Myw1Myw0NSxhLDU3LDEwLDFlLDQxLDQ0LDE3LDE0LGMsYSw1Niw1LDRlLDVlLDQsZSxlLDQsNWYsMTksNCwxNiwxMSw0NSwxNSw1Miw0MCw5LDQzLDQ3LDFmLDQyLDksMWYsNywyLDRmLDIsNGIsNDMsNDcsNTAsNGMsYiwwLDQ5LGUsNDYsNGUsMTQsNTMsNTcsNGMsNTIsNDksMywwLDU0LDEsMTUsNWQsMWEsNTEsZSw1OCw1ZCw1YiwxYSw1Miw0Miw4LDQsNWIsMyw1NSw4LDQsMixkLDU2LDRhLDQ0LDQ4LDE3LDcsNTgsZiwxLDE2LDgsNDIsNWEsMjcsYSxiLDQ5LDFhLGUsMTAsMCw1OCw1ZCw1Myw0MCw1MSw1ZSw1YywxNiwzLDViLGEsNTQsMWIsMTgsMTgsMTksNDMsM2QsYSw1NCwxNSw0NCwxNyw3LDQyLDIsNDIsNTAsMCwzZSw0NSw1MCwxYSwxOCwxMCwxNiw1Ziw1Yyw1NCw0MSw1Yiw0NSw2MSw0MywzLDEwLDVlLDEyLDEsMSw4LDUxLDUzLDU3LDU0LDIsNDMsMSw0MywxNSw3LDMsNjksNDYsYywxNSwwLDVmLDFhLGUsNTQsNyw0MSw0MCw1NSwxOCwxYSw0Miw1MSw0NCw0LDU3LGEsNjAsNTIsNDMsNTksZiwxMCw0NCw1ZSw0ZSw0Myw1YSwyOCxjLGMsNCw1Ziw3YywwLGEsMiw0NSw0YywxNiw4LDU3LDE5LDUsMiwxOCwxYSw0Niw3ZCw0MywxNSw1NywxNiw3OCw1Niw1OCw1ZixhLDE3LDQ0LDVlLDQsNTIsMTQsNTMsNGUsNDAsMTYsNjIsNDEsMTEsNiwxNyw3YSw1MSw1MCw0NixlLGYsOSwzLDAsYywxLDFlLDE0LDE2LDdiLGEsNWUsNTYsNDMsNmYsYiw3LDEyLGMsMTcsNWIsMWYsNTUsNTMsNTcsNGQsZiw0MywzNiwwLDE3LDQ4LDVkLDVhLDZhLDQ0LDE3LDMsMWMsMTYsNGYsNjEsNTMsNTEsNCw2YSwyYiw1Niw1NSw0Miw1ZCwxNiw0MSw1Yyw1NCwxOSw0Myw1YSwzMSwzLDUsNCw3NCw3YiwzLDUsMTYsNDgsNGMsMTYsOCw1NiwxLDExLDUzLDYzLDUxLDU1LDQ2LDVlLDQzLDgsNTYsNCwyLDcsMTQsNDAsMCwyZSwxLDVjLDYsNDUsMTUsNDAsNTgsNTAsMTksMiw1Nyw0Ziw0Nyw1ZSw2Ziw1ZCw1NiwxMiw0NSwxMSxhLDcsYyw1LDIsMWEsNDMsNDEsMmMsNTUsNWEsNTYsNTAsMTYsNDEsNWMsNTUsMSw1NSwxZCw0ZCw0MCwxMSwyMCw1Yiw1NSxjLGYsMzIsNDQsNWMsNDAsNWEsNDQsMTcsMCw0LDAsOCwxZCwxMCw0NSwyMCw0NCw1LDU5LDVmLDc5LDVkLGIsNCxlLDEwLDE3LDViLDFjLDUyLDViLDUwLDRkLGYsNDcsMjYsYyw5LDQyLDRhLDcwLDU3LDE2LDU5LDViLDEyLGUsYSw1LDFlLDE0LDEyLDYyLGQsNDgsNTYsNWQsN2MsNywxMywxMixjLDE3LDViLDFmLDU1LDRlLDQwLDE2LDY5LDUxLDEzLGEsNiw0OCw2OCw1ZCw0YSwzLDQxLDYxLDUxLDQwLDUxLDVlLDEwLGMsNTEsMWMsNWMsOSxhLDgsMSw1Yiw1YSw1MSw1Miw0LDU0LDE1LDUwLDU2LDUwLDUwLDEsMTYsMTIsMjAsYSw0MSw1Nyw0Niw3NSw3LDQwLDQ2LDQ0LDE2LDIsNmEsMTAsNTcsZiw0Yiw0Niw2ZCw0ZSwxZCwxYSwwLDExLDksMTMsNDYsNCw1ZiwzNyw3LGMsNSw0Miw0Niw0Nyw1OSw0Nyw0ZSw1MCw0Niw1ZCxiLDQ4LDExLDFjLDE2LDVhLDQzLDVkLDQxLDEyLDU3LDE2LDc1LDVkLDU2LDUxLGMsNiwzMiwxZCw0NSw0LGYsNWIsNDAsMSw5LDVmLDViLDgsYSwxMCw0MCwxYSwxOCwxMCwxNiw0MSw1Miw0NCw1Miw1Nyw0Myw1ZiwxNCw1YiwxMCwzMyw1OSw1ZCwyLGEsNDAsNGYsNDQsMTcsNDUsNCw0OCwyLGEsMzEsMTgsNDMsNDAsZCw2LDE2LDQ0LDRiLDE2LDgsMWQsZiw0NSw1Ziw1ZCw1Yiw1NCw0MSw3NSxlLDQ3LGEsNDQsMTEsYiw4LDRlLDQxLDIsMSw1MywwLDU4LGQsMTYsMzEsMTEsNDgsNTEsNixiLDMzLDQyLDUxLDU3LDU3LDQ0LDE3LDExLDQ1LDVhLDVjLDU0LDU0LDVmLGYsNTcsMCwxMiwxZiwxMyw1NCxkLDAsNyw4LDY2LDQsNWYsMTcsYiwxLDQsN2IsNWIsYywwLDAsNWUsNzksNTksNWQsMTMsNDMsNDcsMTIsZSw4LDFkLDEwLDUxLGUsNWQsMyw1Yyw1Niw2Nyw1NyxiLDAsMywxNyw3NCxjLDQyLDE0LGMsMTYsNDMsMTcsNCwxOCw0Ziw0Nyw1OSw1MSw1OSw1NywxYyw0Miw1ZCw1NSwxNiwyLDEzLDc3LDQzLDEzLDVkLDE0LDU1LDFjLDdjLDU3LDExLDAsOSwxMywxNyw0ZCxmLDAsMTcsNiw4LDQyLDc3LGEsNywwLDRlLDRiLDE2LDgsMWQsZiw3ZSw2MCw3LDFhLGIsMTAsNDYsMTMsNWQsNiw1MSw1MSw1ZCw0MSw0MCw0Ziw0NCwyNSw3NCwyMixmLDViLDQwLDEyLDEzLDQyLDU2LDQsMSw5LDU0LDFhLDE4LDEwLDMxLDZjLDY1LDEyLGUsMWEsNWMsNTMsNGYsMyw1Nyw0NiwxYywxMSw3ZSw3ZiwyNSwzYywzMCwyYiw2NywyMyw2NCwzMiw0MCw1OCw0Myw0MCw1NSwxYywxLDAsZiwxNCwxNiw3ZCwzNiw3OCw2MCw2Ziw3Yiw3Ziw3NiwxMCxjLDQzLDQyLDE2LDVmLDUxLDUwLDVhLGUsMWEsNDQsNDgsMTcsMmUsN2QsMzQsMzEsM2QsMzYsNjgsNzYsMjgsNDEsNWYsZiw0OCw0Niw1ZCw0LDRjLDUxLDVjLDRkLDFhLDFkLDEwLDcwLDJkLDczLDI3LDEyLDksMTMsNDgsMTAsYyw0LDUsNTcsZCw1NCw0Myw0ZSw0MCwyYyw3ZCwwLDQ3LDU5LDQ3LDVkLDRhLDViLDUwLDcsNGYsNWYsNDksMTYsMTQsMTMsNjUsNzMsMjMsN2YsNDYsYSwxMSw1Yyw1OSwxYiwxLDMsNDYsMTksNDMsNjAsMjgsMjYsMmIsNDMsMTcsMTYsNDcsMWUsNDksZiw0ZSw1ZCw1NiwzLDQyLDcwLDVmLDUwLDVkLDUyLDQxLDE0LDViLDQ5LDQ2LDdkLDYzLDUsMWEsNTgsNDEsYiw1LDRjLDMsNDgsNDMsNGUsNDAsMmMsN2QsMCwzYSwyMSwyNCw3ZSw3ZCwxNiw4LDQ0LDVkLDQxLDVmLDU2LDU5LDUzLDVlLDRmLDQzLDFlLDQ2LDdkLDYzLDUsNjcsMmEsMmEsMjEsMmMsMTcsNWIsZiwxMSwxMCxkLDMsNGMsNTYsOSwxYSw0NywxLDFhLDYzLDc3LDI0LDYwLDExLGEsMTYsNTUsNTAsNGIsNTQsNCwxMCw0OCwxMiw2NCw3NCw3YSwyZiwzYywzMCwzNCxkLDQzLDE3LDQzLDEyLDEwLGUsNGYsNTUsNyxmLDFjLGYsMTQsMTYsNjUsMjMsNmYsN2UsNmYsNjIsNjgsOCwxMCxjLDQzLDQyLDE2LDVmLDUxLDUwLDVhLGUsMWEsNDQsNDgsMTcsMzYsNjgsMjMsMmYsM2QsMzcsN2QsYywzYSwyYywzNSw3OCw2YiwxNiw4LDQ0LDVkLDQxLDVmLDU2LDU5LDUzLDVlLDRmLDQzLDFlLDQ2LDdmLDc0LDc2LDFhLDU4LDQxLGIsNSw0YywzLDQ4LDQzLDRlLDQwLDJlLDZhLDczLDNhLDM3LDJkLDY4LDc3LDY2LDczLDM5LDdiLDdjLDYyLDc2LDcxLDYyLDEwLGMsNDMsMTAsNDgsMTIsN2UsN2EsNmUsNDAsNTksNDQsNDYsMTksNDMsNjAsMmEsMzQsM2QsMjksNjQsNzMsMmQsNDEsNWYsZiwxYSwxOCwxMCw1NSw2YSw2MywxMixlLDFhLDVjLDUzLDRmLDMsNTcsNDYsMWMsMTEsMiw3ZiwzMiwzMyw1NCw0NixmLDQzLGYsMWMsNGUsNDAsOCw0Yiw0Niw0LGUsMCxmLDIsNGYsMTAsMTEsNDgsNTEsNTQsNDYsNTEsNDcsNTcsNDQsMjgsNWMsMmQsNTYsNDEsNTAsNTUsNyw0MSw1YywyLDU0LGQsNWUsNCw0ZSw0MCxlLDViLDUxLDE3LDExLGMsNDksNWQsNWEsMyw0NCwxNyw1NSw1MSw1OCw0Yiw1NCwxZSwxNCxlLDQ0LDEsNDIsNDEsNTgsNWMsNyxkLDU0LDQ2LGYsNyw0YyxkLDExLDcsNGQsZiw1YiwxMyw2LDE3LDVmLDUxLDUwLDU3LDgsMWUsMTEsYSw1Miw1OSw1ZCw0MSw1MywxYywxZSw0Niw1Niw1Yyw1Ziw0YywxMSw0MSw1YywzZiwxNywyMCw0YSw0LGMsMSwxOCxkLDcyLDI3LDQxLDQ5LGYsNzksNDYsNWIsNyw0MSwxMSwxYywxNiw3Yiw1MCw1ZSw1ZiwzLDQwLGQsMTIsMWYsMTMsN2IsNyxkLDEyLDExLDQ3LDE4LGQsMjYsZCwxNiw5LDQ0LDU3LDQ3LDRmLDQ3LDZlLDVkLDVhLDQ2LDEzLDVmLDRhLDEyLDE4LDFhLDc3LDQwLDU3LGYsNTksOCw1OSw1ZCwxMSw3ZixkLDE3LGUsZCw1Niw0MywxLDQzLDJhLDMsNCw1OSw0MCwwLGQsMTYsNGUsNTAsNDMsNTcsZiw0MSw1Niw0MiwxNiwxNCwxMyw3ZSw1Myw0LDVlLDUsNDcsNTIsNTUsNWQsNyw0MSw0YSw0Niw3OSwxNCw0ZSw4LDYsMyw0MSw2Ziw0NixjLDQsZCw1OSwxYSwxOCwxMCwyYSw1OCw1MCw1OSw1MCw1OSwxMSw2MSw1NyxmLDQxLDQ2LDFjLDExLDdjLDZiLDQyLDJjLDEzLDEwLDU5LGUsNDIsYSw0MCw0ZSw0Myw2MCw2Nyw0NSwzMSwwLDRiLDVkLDQ2LDU3LDgsNGUsNTYsMTAsNjcsNDgsNTQsNTEsNWYsMCw1ZSwxMCw0OSwxMSwxZCwxYSwyZiwzMCw0NiwzMSw3Yyw0MSw2YSxlLDE2LGEsOCw0ZSwxNiw0OSw0MSwyOCw3OSwxOCw3MSw0YSwxMiw1Ziw1MiwxMiwxOCwxYSw3Yyw1Myw0NCxkLDU3LDEwLDQ0LDExLDFkLDFhLDJmLGEsNSwxNiw1YSwxMiw0Miw3LDE2LDQyLDM0LDQ0LDUzLGQsMTYsMTcsZiwxNCwxNiw3Ziw5LDQzLDVjLDQ0LDRkLDQ4LDU0LDEyLDc1LGUsNDAsMTcsNTksNDUsNTAsMWEsNGUsNDEsMzYsMTYsNWMsMTIsNTksOCxjLDMsNDMsMSwxNiwzNiw2LDIsNDIsNWQsMTQsNjcsMmYsZCw3Ziw1OSw1Myw1MCw0NSwxMCwxYSw0Myw3MywxNiw1OSw1Miw1ZCwxOCwyMCxmLDcsNyw1ZSw0MywxLDQzLDIzLDEwLDgsNGMsNTgsNDUsMmQsNCw1Ziw0YSw1Yiw0NSw0NCwxLDExLDcxLDQ2LDUxLDUwLDVlLDE2LDMzLDVkLDExLDVlLDU3LDU0LDVjLDQyLDJlLDMyLDQ2LDE5LDQzLDZlLDAsZSxiLDMsNWYsNWQsNDcsNGYsNDcsNmUsNTksNWEsNTYsNyw1Ziw1MiwxMiwxOCwxYSw3Miw1Nyw1OCwxNSw0NywxNiw0OSwxMyw3Niw1NywxNixiLGYsNywxNyw0ZCxmLDIyLDcsYywxNSw1OCw0NiwxYyw0MSw0OSxmLDdiLDViLDVmLGYsNGUsMTMsNjMsNTUsNTYsNDIsMTIsN2IsMzIsMTAsNDgsMTIsNzAsNWUsNTYsMTEsMTcsNyxhLDQxLDgsNGMsNDMsNGUsNDAsMjIsNDIsNDEsMTcsYSwwLDVmLDE4LDdhLDU3LDExLGYsMWYsMTIsNzcsNTcsNDQsNDAsNWYsNCw0MCw0NiwxYywxMSw3Nyw0YSwzLGQsZCw4LDVjLGYsZCwyNixkLDE2LDksNDQsNTcsNDUsMmUsMCw0OSw1MSw0MSw1Ziw0NCwxLDExLDc3LDU1LDRhLDUwLDVmLDU5LGYsNTYsNDYsMWMsMTEsNzYsNWQsZCwxMSwxLGQsNTQsNDMsMSw0MywyYSw3LGQsNWIsNTEsMTEsYSw2LDRjLDFhLDE4LDEwLDJmLDQwLDQzLDUxLDU3LDRjLDEzLDFlLDE0LDJkLDQ3LDcsNTksNTcsNTAsMTgsMjAsMTEsZiwzLDVkLDE1LGYsNGQsNDAsMmUsMTQsNGUsNWQsMSwyLDQ1LDZlLDU3LDVhLDQxLDksNDEsNTYsMTIsMTgsMWEsN2QsNDcsNTUsOCw1Niw1LDEwLDYwLDUwLDU2LDExLDQzLDMzLGEsNWMsMiw0Miw1LDcsNDAsNGQsZiw2NCwwLDExLDE1LDQ4LDRjLDQxLDUzLDQ0LDEsMTEsNjIsNWIsNWIsNWEsNDUsNTMsZCw1ZSw0NiwxYywxMSw2Miw1ZCw1LGMsMyw0NCw2NSwxMyw0NCxmLDE2LDQwLDRkLGYsNjcsMCw0LGEsNDgsMTgsNjcsNTEsMTQsNDQsNDMsNDQsMTYsMTQsMTMsNjEsNTMsNiw1ZCwxLDEwLDY2LDc4LDFhLDRlLDQxLDMyLDUsNWQsZSw0MCwwLDQwLDRlLDQzLDc5LDVkLDgsNiwxNixkLDc2LDUxLDQ1LDQ2LDdmLDVjLDVkLDU1LDU2LDEzLDFlLDE0LDM1LDViLDksNTUsNDAsMTMsMTQsNDAsMzcsMTQsMSw1NywxNCw0ZSw5LDcsMTYsNDEsNjAsNjcsNDcsNGYsNDcsN2IsNWQsNDYsNTYsNyw0Myw1MiwxMiw2OSwxNCwxMyw0Nyw0NSw0LDQwLDI1LDU3LDU2LDVmLDRjLDI2LDIsMTIsNSwxNyw1Yiw1Niw0MywzLDEwLDIsNDUsNWQsMTEsNiw2LDU5LDRkLDQ2LDU3LDQ0LDE3LDExLDQ4LGMsZSwxMywxZSwxNCwzLDViLDEwLDVlLDU2LDQyLDRiLDQwLDU5LDQ0LDUyLDEsNDMsMSw0MywwLDEwLDAsNDMsNTAsMTYsNDEsNWYsNzYsNDMsMTYsNTAsMTQsNGMsNWQsNTQsMTYsMiwxMyw3Yyw1OSwxNSwxMiwyNSwxOCw3MSw0Myw1OSxjLDcsNDQsNDgsMTcsMTcsNDgsMTMsMTEsYixlLDQzLDE2LDVmLDQxLDVkLGYsNDUsMTgsNDksNDQsNGYsNDEsNTEsNWEsNWMsMTMsOCwxNCwyMiw1YSwxNiw1Ziw1ZSw1OCw0ZCxmLDQxLDRhLDQ2LDQzLDQsNWYsMTIsYixkLGYsZixlLDQ3LDUyLDU2LDFmLDFhLDQ5LDFlLDFkLGYsNTEsNDIsNTUsNTYsNTUsMTAsYyw0Myw2Yiw1LDcyLDQxLDVlLDRmLDExLDYsMTQsNDYsMTksNDMsNWIsNCwxMCwxMSw4LDQyLDVhLDQ3LDU5LDQ3LDFmLGQsMWEsMCw0NCw1MCwxZiw0YiwxNiw1YSw0Myw1Myw1OCw1LDEwLDVlLDEyLDZhLDVlLDRmLDExLDYsMTQsNDYsMTksNDMsNWIsNCwxMCwxMSw4LDQyLDVhLDQ3LDU5LDQ3LDFmLDE2LDEsMTAsMWIsNzAsMWYsMTIsNTIsNGQsNWQsNWUsNjAsNCw0MCwxNyw1OSw1Yyw1Ziw3NCxiLDEwLDEyLDQ2LGYsM2EsNTYsNDMsMCwxMCwwLDQzLDUwLDQ3LDU5LDQ3LDYzLDU3LDQwLDEyLDI3LDUsNzEsNDIsNTUsNTYsNTUsMTAsMWEsNDMsNDQsMSw0Miw0MCw1OCw1NyxjLDQxLDVjLDQ2LGQsNGYsMWQsNGYsNTIsNGMsNTEsZiw0OSw0OSwxOCw0Nyw0Ziw0YSw1NSw1YywyLGYsOSwxMiw3Nyw1MCw0Myw1ZCw1Yiw4LDQ3LDksMTIsMWYsMTMsNGUsNywxMSwxNSxkLDVhLGYsZiw1Yiw0MCw1Myw1MiwxZiwxYSw1NSw0ZCw1MywxNSxiLDAsMWMsNTAsMTQsNCwxMiw0OSwxNCw0YSwxMCw1NCwxMyw1MyxhLDU0LDExLGIsMWEsM2IsMiwyNCwxNiw1YSwxNiw1ZSw0LDEwLDQwLDRkLGYsNDIsMCwxMSwxNiw0NCw1Nyw1YSwxMCw1YyxmLDEsNSwxYSxhLDFmLDQsMTgsNTcsYiw1MywxMiw0ZSwxZCw0Myw0MCwxLDE0LDUsNWIsNSxmLDViLDQwLDNiLGUsNWEsNDcsMCwxMSw0NywxLDFhLDQyLDU3LDE0LDVlLDVhLDVmLDVhLDFhLGIsMTAsNCw0Ziw3LDQ2LDRkLDZlLDFkLDFhLGYsYyw0LGQsNTksNCxmLDViLDQsMyxkLDVlLDUxLDQ5LDQxLDgsNDIsNWMsNTEsNWUsNDQsMTcsMTEsMTIsMTgsMWEsNDEsNWUsNTcsMTUsNTQsYiw0Miw1ZSwxMywyLDQwLDM0LGYsYSw1MSxlLDVhLDEyLDQwLDRlLDQzLDVkLDU4LDQsMTcsMyw0Miw0YSw1OSw2NCwzLDVmLDQwLDU5LDViLDU2LDEzLDgsMTQsNTAsNyw0YSwwLDFkLDEsMWEsMWYsNGYsNDQsZiw1MCwxOCw0ZixlLDMsMTAsNSxmLGUsMWUsNDEsOSw0Yyw0MSw1Yiw0NywxMiw2MCw1Miw0MCwxNiwyLDEzLDc5LDUzLDE4LDc5LDQ4LDViLDEzLDdhLDVkLDFiLDI0LDRhLDMsMTUsMjUsNDQsNixiLDE2LDUzLDEsNiw0NSwyNyxjLDRhLDUxLDQwLDIsNGEsMWQsMTMsN2IsNTEsNDEsNjcsMWUsNDAsNDEsNzksMSw0OSw3MiwxZCw1OSw0MiwyMSw3LDcsNWUsMTAsNTgsZSwxNiw3LDRkLDRkLDE0LDJlLDYsMWMsNjEsMTQsNTgsMTIsMmYsNDMsNDcsNWMsNzYsNTksNTIsNTksNDUsZCw1MywxNyw1OCwxZiw2ZCw2NCw0MiwzMiwxMyxiLDQxLDQsMSw0Niw0MiwyOSw0LDU0LDYzLDQ5LDE0LDQ1LDY5LDUxLDUzLDViLDEyLDE1LDFmLDgsMTQsNzMsNTQsNGIsN2IsNGQsNWYsNDQsN2IsNTYsNDgsNzAsNGUsYiw0NiwzNCw1MCwxMyw0NCxlLDYsNGUsNGYsZCw3MCxjLDQsYyw1OSxmLDE4LDUsNDYsNjksNWEsNTcsNWQsNGMsMCwxZSw3LDQxLDc5LDEsNDksNjMsMWQsNDgsNDIsMjgsMywxZCw3MSw0ZCw0OSw0MSwyOSw3LDE4LDZiLDE4LDMsNDMsMmUsNDgsNDEsN2IsMWUsOSxkLDc4LDU1LDRkLDY5LDFkLDQzLDE2LDJhLDU3LDFkLDczLDFmLDUyLDE4LDI5LDYsMWYsMmEsMTksZixkLDIzLDEwLDMsMiw0Niw1MSwxMSwyZiwwLDRiLDRjLDE4LDY5LDQ2LDY2LDU2LDQ5LDZlLDE0LDRiLDEyLDdkLDQsNGIsM2QsMWMsNGEsMTEsN2MsYiw0LGYsMTAsNiw0ZCwxZSw0MSwyNixiLDYsNDQsNDAsNTMsNGYsNTMsZCw3Yyw1ZCw1NSxmLDU5LDYsMWMsMSwxOCw3YSw1Nyw0ZiwzOSwxZSwxYywxMCw2MCw1ZCw1OSwxMSxiLDRhLDRiLDE1LDIzLDRjLDIsOSwxMSxkLDRjLDQ3LGQsNGYsMzksNzEsMTgsNzcsNWQsYiw0MCw1MiwxYywxOCwxOCw3Yyw1Yiw1OCwxNCw0MSw0OCwxZCwxMyw3NSw1MSw1LGEsMTIsNTAsMTksNTUsZCwyYSw3LDFiLDIzLDEsNTYsNDUsMjgsMCw1NCw2YywxOCw0Niw0Niw2OSw1YSw1Nyw1ZCw0Yyw4LDFlLGYsNDEsNzksMSw0OSw2MCwxZCw0Yiw0MiwyOCwzLDFkLDdjLDRkLDQ0LDQxLDI5LDcsMTgsNzgsMTgsMTAsNDMsMjAsNWMsNGQsNTUsNWUsNGEsMTAsMTMsN2IsNTEsNDEsN2IsMWUsNWMsNDEsNjEsMSw1ZCw1YSw1Miw1NyxlLGMsOCw0OCxlLDQxLDY2LDQsMWIsMzAsNGQsNWYsMTQsMjcsMTEsNCw0ZSw1Myw1MSw0NiwzNCw0NCw1NCw1OCw0MCwxNCw2YywxMiw3ZCw0LDRiLDIxLDFjLDU2LDEzLDE0LDQwLGYsNywxZCw1YSwxNCw1OSwzMixiLDE4LDQsZixlLDUxLDUzLDU0LDUwLDE0LDE2LDUzLDEzLDQ5LDVhLDVmLDcyLDUxLDVmLDU1LDUzLDEzLDQyLDE2LDU5LDVkLDQ1LDFhLDU4LDUwLDUwLDUzLDFiLDUxLDFkLDU2LDUwLDU2LDU0LDE0LGMsNTEsNTUsNTcsMWIsMSw3LDFlLDQ0LDQ5LDU2LDQ2LDVkLDViLDU0LDdiLDU4LDcsNWQsNDYsYSw0OCwxMyw1MCwzLDExLDIsMTMsNTQsMTMsNDgsMjIsZCxjLDIsNTgsNDYsMTcsNixiLDRlLDQxLDE2LDgsNTcsMWIsMWYsMTIsNTksNWQsNWMsNWQsNDQsMTgsMTAsNWUsOCwxZiwxMyw0OCxkLGEsOCwxMCw1MCwxMyw3OSw0LDEsYSw0MywxNyw2Ziw0Nyw1LGMsNDMsNWQsMTYsMWUsNDQsNGMsNWQsNDksMTYsNjUsMWQsMTAsNWUsZSw0NCwxLDQyLDY3LDU0LDViLGEsNDEsNWMsM2YsMTcsMCw0MywxOCw0MCwzZiw0ZCxmLDU5LDQsMWIsMzEsNDIsNGQsNTcsNWEsMzYsNDIsNWEsNWUsNDAsNGIsMTMsOCw2LDRkLDEwLDUsNTMsNTAsNTQsNTQsNywxMSw5LDksNTAsMTUsNDgsMTMsNDAsNTgsNyw0Yyw1OCwxNiw2LDQ5LGYsNGIsNDQsNTcsNyw0Niw1Niw0Miw0NywxYSxiLDMsMWEsNDMsNWYsZCw1Myw0MSw1ZSw0OCxhLGMsOCwxLDQ2LDQzLDE3LDUwLDRlLDQwLDE2LDQ4LDU2LDYsMiw4LDVlLDFhLGUsMiwxYiwxLDExLDUzLDU1LDU2LDQ3LDUzLDQ1LDQzLDgsMWYsMTIsNDQsNTgsNTYsNixhLDgsMywxNyw1Yiw1OSwxMywxNyw3LDRkLGYsNTMsMCxjLDgsNDgsNGMsNDYsNGIsNDQsMTcsMTEsOSw1NSw1YSw5LDU2LDU3LDU0LDIsNTAsNTYsYiw1Miw1YSw1Nyw1YiwyLDUsYyw1NiwxZCw3LDVhLDUwLDU3LDE4LDU1LDEsNTMsNiwxNSxkLDYsNCw1ZiwxZCxhLDU0LDUwLDVlLDQsNixlLDU3LDU2LDYsNiw1MiwzLGIsNiwyLDIsMCw1MSw1OCwxZiw1MCw1MSw1NCw1MCwxZSw1MCw1NywyLDQ3LDEsMWEsNDAsNTcsMWUsNTksMTEsYSwxNiw1ZSw5LDQsZiw1MCw1NywyLDcsNiw1LGMsNTIsNSw1Myw1ZCwxLDcsNDksMCwwLDcsNTQsNDgsMSw3LDYsNTEsNGYsNWQsNCwwLDUzLDFlLDUxLDcsNiw1Yiw1MCxiLDIsNTksNyw1MSw0LDMsMyw1ZCw1NCw1Myw1Myw1MCxjLDIsMWQsNTMsNTEsNCw1Myw0ZSw1LDEsNTIsNyw0OSwxYSwxOCwxMCwxMiw0Yyw1ZSw0MCw1MSw0YSw1NCw1NiwxNCw1Yiw1NCw1LDVjLDQwLDU0LDQ1LDRlLDQxLDE2LDEsNDcsYyw0NCwxMiwxMSxiLGUsNDMsNDcsNDcsNTksMWUsZiw1MSw1YSw1MSw5LDQzLDQwLDU5LDQ3LDRjLDU0LDVjLDQyLDJmLDVkLDEwLDU5LDU1LDU4LDViLDMsMTcsZixiLDViLDEyLGYsNWIsNCwzLGQsNWUsNTEsNDksNDEsMTUsNDgsNGEsNTksNWIsMTUsNWUsNWEsNWYsNWEsNGIsMTMsOCw0ZCw0Myw1Myw3LDUzLDU2LDVkLDVkLDEwLGMsYiwxLDQxLDQsNWYsNDMsNTgsNDAsNiw1Ziw1NSxiLDE3LDAsNDksMWEsMTgsMTAsNCw0Yyw1MCw1Yiw1Myw0YSw1ZSw0Nyw1OCw1LDFmLDIsNTUsNDcsNTIsNTAsNDAsNTksNDQsMyw0NywwLDQzLDE1LDcsNiw0MywxLDE2LDcsMiw2LDQ2LDVmLDQ2LDVkLDEzLDQzLDU3LDFkLDQ3LDQxLDVmLDUxLDE0LDViLDEwLDMsNDIsNTIsNWYsNGMsNyw3LDQ0LDQ4LDE3LDIsNGMsYyw3LDEwLDAsZixlLDQ3LDEzLDE3LDQyLDU1LDQ0LDQ2LDQ0LDEsMTEsNTMsNTgsNTEsNDEsNTAsNTksMCw0MCwwLDFkLDQxLDU0LDU5LDYsNDEsNWMsNDYsNDUsMTMsNDIsYywxMiwxNiw0MywxLDE2LDYsZixjLDVkLDVhLDViLDUzLDE0LDQ5LDFlLDQ3LDQ2LDUxLDQ1LDU3LDE0LDViLDEwLDMsNDIsNTIsNWYsNGMsNyw3LDQ0LDQ4LDE3LDUsNDQsMTIsMTIsZSwwLDU0LDE5LDYsMiwxNSw1OSw0ZCw0Niw1Nyw0NCwxNywxMSw0MCw0Niw1Nyw1Yyw0Miw0Miw0MywxZSw0Niw1Nyw0YSw0Myw1NywxMSwwLDksMTQsNTAsNDMsMTcsNDMsNSwxMCwwLDQzLDQwLDAsNyw0NywxLDFhLDUzLDU3LDksNDEsNWMsNTMsNTUsNGMsNTgsNWQsNTgsNDMsOCw0Niw0MCw0MSw1ZSw1NSwxMiwxNyw0NCw0OCwxNyxkLDQyLDIsMyxlLDRjLDRiLDViLGIsMTcsMTYsZiwyLDE2LDQyLDE0LDQyLDVlLDQwLDQwLDFhLDFkLDEwLDViLDAsNTUsYSw1NSw0Nyw1ZSw1NSw3LDE3LDMsMTYsMTcsNWIsZiw2LDEwLDMsZiw1OSw1MSwxLDQxLDQ5LGYsNTUsNWQsNTEsMTQsNDIsNDMsNTgsNWIsNTYsNTQsMTAsYyw0Myw0MiwxNiw1Ziw1ZSw0MSw0Yyw0MCw0Ziw0NCw5LDVjLDUsNDQsNDMsNTgsNDAsMTEsNWYsNWIsOCwxMywxMSxmLDE0LDE2LDVjLDksNTksNWEsNTYsNWQsNWIsNTAsNDYsNWYsZSw1YywxNywxMiw5LDEzLDQ4LDEwLGMsYiwxNCw0MSw0MywxLDQzLDEyLDMsMTgsNDAsNTEsYiwxNyw0OCw0NSw1OSw1YSw1NixhLDQ4LDQxLDEyLGUsMWEsNTYsNDAsNTcsZiw0NiwxLDU0LDExLDFkLDFhLDEyLDYsMTQsMTcsNWMsMTIsNTksNCxjLDE2LDRjLDVlLDQwLGEsMTEsNCw0YSw1ZCwxNiw4LDQ0LDVkLDQxLDVmLDU5LDQ4LDQ1LDEwLDFhLDQzLDQxLDcsNDIsNTYsNTQsNTYsNGYsMTQsNyxmLDUwLDRjLDQxLGUsMSw5LDQzLDE3LDE2LDIsMTEsNCw0Myw0Yyw1MSw1Niw0NCwxLDExLDQzLDQwLDU3LDQzLDUzLDUxLDQsMWYsNSw1Myw1MCw1NCw0YiwxMSw0MSw1Yyw0Niw1MiwxMyw0YyxmLDE2LDcsNSxmLDE4LDQ3LDE0LGMsNDMsNWMsNWIsNDUsNGIsNDAsNTIsNWUsNTUsNWYsNTQsNWYsNTMsZiw0Niw0NixhLDExLDQxLDRhLGQsZSwxNiwxMCwxNywxYyw1MCw0ZCw0MCwxNSxlLDVmLDVmLDAsMTEsNDcsMTcsNDMsMTYsNDUsMyw0Ziw3NCw3Yyw2Miw1ZCw1Ziw1Niw1OSwxMywxMCw1ZSwxMiw3NCw1ZSw1Nyw1LGYsMyw0NCw3YyxmLDRlLDRmLDQyLDRhLDIwLDYwLDcwLDRjLDQxLDQ5LGYsNGYsNTEsNTAsMjEsNjEsNjEsNTUsNWEsNWMsNTQsNDAsNTMsMTMsMTAsNWUsMTIsNzIsN2YsN2YsMmUsMjYsNDYsNGMsNzQsMmMsNjksNGQsNDIsMjMsMmMsNjksMTQsMzcsMiwxLDQ4LDU3LDVhLDFhLDMyLDYwLDFhLDEwLDczLDRhLDUwLDQyLDVlLDgsNTEsMTcsMTAsMWIsMSw0MCw1Miw1Myw1Niw1NCw0LDU3LDFlLDU3LDRiLDQyLDI1LDQ0LDQ2LDAsMCwxMSwxZSw3Yyw1LDMsNDYsNWIsNDAsNmYsMSw2NywxLDEyLDQ2LDEyLDZkLDUxLDZmLDMsMWQsMTgsMjYsNTAsMjIsNTUsNCw0OCxmLDRkLDQwLDE3LDEyLDQ4LDQ2LDI0LDQsMCw0Myw0YywxNiw4LDQ0LDYwLDVjLDRhLDVkLDU0LDVkLDUzLDE5LDU0LDFjLDU0LDEwLDFiLDY2LDUxLGMsNyw5LDEzLDQ2LDQxLDYzLDM1LDQyLDUzLDUxLDMsNCw1ZSw0MywzMiw0NCw1NiwyLDYsNWQsZCw0Yiw2LDAsMTEsMTEsNzMsNDYsMTEsNWUsMSw2Nyw1Niw1Myw3MyxiLDE3LDQ5LDUxLDYsNTYsMyw1Miw1NCw0Miw0OSw2Niw3YywzMSwyZSwyOSwxLDE4LDU4LDViLGQsNDgsMTMsNzcsNTEsNWIsNWEsNWQsMWYsNDEsNzEsYyw0Miw1Yyw1Yyw1ZCw0ZCw1Miw1NSw1NiwxYiw1MSwzLDUxLDRjLDUyLDQxLDc0LDU1LDI3LDExLGEsNWEsNGIsNTEsNDAsNDksMWYsNiwxZSw2LDE2LDEsMWMsNiw0MSw2MSw1LDU2LDUyLDQzLDUxLDRkLDU2LDU1LDUzLDFiLDUyLDFiLDQzLDRlLDQwLGQsNGMsNWEsMiwxNiw0LDRhLDVkLDQ3LDEwLDVjLDc2LDExLDQyLDQxLDFhLDFkLDEwLDUzLGYsMTAsMzksMWMsMTEsNDEsNTQsMywxNywwLGIsNDcsYyxmLDViLDQwLDM1LDgsNDMsNyw1Nyw0MSw0OSxmLDUwLDU1LDQwLDIsNWEsNTIsNDIsNTEsN2IsNWUsNWMsNTUsMTQsNDAsMTYsNTUsNWQsNTIsNDEsNDAsNTksNTcsNTIsMTksNDMsNGUsNSwxMiwyMSw5LDQ4LDU3LGUsMzQsNDcsMTcsNGMsNDYsNDcsMywxLDExLDU5LDQ3LDdiLDVlLDVjLDQ1LDgsNDEsMTAsNTUsNWQsNDUsNmYsYiwxNyxlLDI5LDU0LDgsNDMsMzUsYSwxMCw0LDRjLDUwLDQ3LDU5LDMsNGMsNTQsNDcsNTcsMWIsMSwxMSw0Nyw1MSw1YSw3Niw3ZSwxNCw1Yiw0OSw0Niw1Nyw0Myw0NCw3OSw2LDIsMTYsMTAsNTAsMTMsNjQsZiw0LGQsNDMsMTcsMTYsMzEsMWEsMTUsNDgsN2QsNDYsNDAsOSw1Ziw5LDEwLDUyLDYzLDU5LDFhLDE4LDRmLDFjLDRkLDZkLDEzLDU4LDRiLDQyLGQsOSwxMCwxNSwwLGQsNywxNyxjLDIsNTksNWQsYSxkLDQ3LDEsMWEsNTMsNDIsMTMsN2UsNDYsNDAsNDQsNTcsNDMsNDYsNTMsNSw3ZSxkLDVkLDVhLDQ1LDRiLDQwLDU5LDFkLDE5LDE5LDQzLDRmLDAsMTEsNywyOCw0Myw1MixhLDQxLDVmLDU2LDFhLDQyLDU3LDE0LDVlLDVhLDVmLDVhLDFhLGIsMTAsNjEsNCw1MCwyMyw3YywxMywwLDE2LDUyLDQzLDRlLDJiLDQ1LDQsNDMsMjYsMmUsNDIsMjQsN2UsMTQsNTcsNGQsNTUsZCw3Yiw1Yyw0MCw5LDQwLDVhLDQ1LDU5LDExLDEzLDFlLDE0LDE3LDU3LGEsNTQsNWMsNDMsMWEsNTgsNDEsMzEsMSw1NywyYSw0NCwxNSw0MCw0ZSw0Myw1Ziw1MSxiLDcsMCw1Ziw1ZCw0NiwxMCw1YyxmLDY0LDU1LDU2LDczLDU4LDQ2LDE2LDM2LDU3LDYsNzcsN2YsMTMsMTQsNDAsMTYsOCw5LDU0LDEyLDQ2LDQsNiwzNCw0LDQzLDUwLGEsMTEsNDcsMTcsMWEsNzMsNWQsOSw0YSw1Ziw1NSwxNCw3MSw1Ziw1MSwxOCw0MSwxYSwyNSw3ZCw3NywxOCwxYSw0ZSw0MSwxMyxhLDU4LDAsNWUsYSw3LDYsMzMsNDgsNWEsMSw2LDE3LDQ4LDRhLDE2LDgsNDQsNmMsN2QsNzcsNzgsN2QsMTEsMWEsNzcsMmMsNzYsNDgsMTAsNzIsN2MsN2MsNDIsMzEsNywwLDUwLGUsNDMsNDksMzYsMmYsNDgsZCw3MywxNywyLDE1LDQ1LDUxLDU3LDQxLDQ2LDUsMyw0OCw0LDgsMSwyLDcsNTcsMSw1MiwxOSwxMyw3NSw1MSwxMCw2LDUsMTAsNiwyNSwxYyw1MCw0MiwxNCwxMiw3MiwxLDNhLDUzLDQ1LDVkLDRiLDZiLDcsMzksMWQsMWYsMTAsNzAsYiw3NSwzLDcsNDgsMTAsNDgsMTIsNDAsNTksNTksNixhLDgsMyw3OSwwLDQzLDYsMTcsMyw2LDQ4LDYyLDAsMTEsMTYsNDQsNTcsNWEsMTAsNWMsZiw2NCw1NSw1Niw3Ziw3ZCwxMiw3MSwyZCw2MSwyOCwxMCw3Niw2MiwxOCw1Myw0ZCw1Niw0NCwxZCwyZSw1ZCw0LGMsMjUsMmQsZCw3MSwzNiw0MywyMiw2MSw2Yiw3OCwxMiwyMyw3ZSwxMywxLDFhLDgsMTEsNzEsNWUsMTMsNWQsOSw1OSw0Niw1YywxMSw0MCwxZSw0YSw0Niw1MywxMSxmLDViLDQwLDAsNTcsMWEsMCw1MSwwLDUxLDRmLDVjLDEsMiwyLDQ4LDU3LDUxLDU1LDgsOCw1MCw1NSw1NCwyLDUwLDUyLDMsNTAsNWUsNWIsNTcsNTAsNSw0LDMsNGIsNTYsNTQsMyw0LDRlLGQsNTIsNiwzLDRiLGQsNTAsNCw1NywxZCw1LDYsZCxhLDUwLDU3LGUsNCwwLDU3LDAsNyw1NywxLDVhLDQxLDFiLDQ4LDE3LDEyLDRlLDEzLDcsNyxmLDFmLDE2LDVmLDE4LDQ3LDViLDU5LDU4LDQ3LDMsZiw5LDRiLDE2LDViLDU1LDQyLDE0LDViLDQ5LDQ2LDUyLDExLGIsMWEsYSxjLDQ0LDQ4LDE3LDE1LGYsNWIsNDAsNTMsNDMsMSwxNiwxNiw0MSw1ZiwxYyw0NSwxOCwxMCxmLDQ4LDQwLDEyLGUsNDMsMTMsNTAsMTQsNWIsMTAsMCw1OSwxMSwxZCwxYSwxNiw0MSw1Yyw0Niw0LDUxLGYsNGQsNDAsMTEsNDMsMTcsYywxOCw0Ziw0Nyw0Miw1Niw0NywxMCw1Yyw1NiwxMSw1MiwxNiwyLDEzLDVmLDU3LDQzLDFlLDQ2LDQ0LDExLGIsMWEsNTYsNDEsNGEsNDYsNDYsNDMsMTcsNTUsMWYsNGUsNDMsNDQsNWIsYiw0MSw1Ziw1NiwxYSw1NiwxMCw1YyxmLDUyLDQyLDE2LDE0LDEzLDQ2LDE0LDViLDEwLDUzLDEyLDFmLDEzLDRiLDQwLDU5LDU3LDE5LDE5LDQzLDU5LDEzLDExLDQwLDViLDU2LDE2LDcsNDEsNWYsZiw1OSw0NiwxMCw0YSxmLDQ3LDEyLGUsMWEsOSwxMCwxYSw0Myw0MSw0NixhLGEsNGMsMTQsNDAsMiw1LDEsMTcsNWIsNTYsNDMsMCw0MCw1YixmLDU1LDE1LDQxLDQ5LGYsNGMsMTYsOCw0NCwxYywxLDEyLDE4LDFhLDQyLDEwLGMsNTEsNGYsNDgsMTIsNTQsNDUsNTAsNDAsNTksMWQsNDYsNTcsNDMsMTcsNDMsNiw3LDQzLDEsMTYsMTEsNDEsNWYsZiw5LDUsMTAsNGEsZiw0MCwxMixlLGEsNGMsMWUsMTQsMTcsNTcsMTYsMTIsOSw0YSwxYSwwLDQxLDVjLDQ2LDUxLDQsZiw0ZCw0MCwxNiw0MywxNywxNiw1NCw1NSw0NywxLDFhLDQ3LDEwLDVjLDFmLDRlLDFjLDE2LDVkLDVmLDQ2LDE0LDViLDQ5LDQ2LDUyLDExLGIsMWEsMywxMSw0NCw0OCwxNywxNSxmLDViLDQwLDUzLDU3LGYsMTgsNDcsMTAsNDcsMTcsZSw0OSwxZSw0NCw0Ziw1NCw1YywxNiwyLDRhLDEwLDU0LDQzLDgsNDYsNWQsNTIsMTMsMTQsNDAsMTcsNDQsNWUsMTcsNTAsMWMsNDMsNGUsNDAsMTIsZixlLDU1LDFlLDQ5LGYsNTEsNWEsNTYsNDQsMTcsNDgsMTIsNTYsMWEsYiwxMCw1YiwwLDEwLDQ4LDEyLDQ3LDEzLDIsNDAsNTIsNTMsNDYsMTksNDMsNWUsNDMsNTgsNTEsMWMsMSwxNiwyLDYsMTYsZiwyLDRmLDEwLDQsZiw5LDEyLDU5LDU5LDEzLDFlLDE0LDE1LDEwLDVlLDEyLDUsMTMsMTQsNDAsMTAsNDQsNWUsMSwxYywxLDQzLDEyLDcsMTIsZixlLDFlLDQxLDcsZiwyLDE2LDU2LDMsZiwxZiwxMiw0MCwxYSxiLDEwLDcsNTcsMTAsNDgsMTIsNDAsMTMsMiw1NSwxZSw0YSw0Niw1YyxmLDVlLDQzLDU4LDE5LDQzLDRmLDE2LDVmLDQxLDQsNWYsMWEsMTgsMTAsMTIsZiw5LDEyLGQsMWEsMWQsMTAsNDUsNDMsOCw1MCw0ZCwxZiwxMyw0YiwxNywxLDQ0LDVlLDRlLDQzLDRmLDQzLDU4LDQwLDUsNDQsMTYsNDksNDEsMTEsZiwyLDE2LDMsNTMsZiwxZiwxMiw0NywxYSxiLGIsNGIsNGQsMTAsMSw1Myw1OCwxMywyLDE5LDQxLDQsNDYsZiw0Myw0OSw4LDQwLDRlLDQzLDU5LDE2LDVmLDQxLDU1LGYsMTQsMTYsNDEsNDQsMTcsNSw0ZCw0OSw0NSw0Yw=="                },
                    "action": "auth",
                    "userScope": {}})
                print(f"🔐 2️⃣ Token попытка #2 — статус: {response.status_code}")
                print(response.text)
                try:
                    resp2 = response.json()
                except json.JSONDecodeError:
                    print("❌ Невалидный JSON (второй ответ):\n", raw2)
                    return None
                if resp2.get("code") == 498 and "challenge" in resp2:
                    payload = resp2["challenge"].get("payload")
                    if not payload:
                        print("❌ Payload отсутствует в challenge!")
                        return None
                    print(f"⚠️ Challenge required — пробуем повторно с payload: {payload}")

                    # Повторный запрос с payload
                    command = ["node", 'starter.js', payload]
                    result = subprocess.run(command, capture_output=True, text=True)
                    if result.stderr:
                        print("Ошибки:")
                        print(result.stderr)
                        return None
                    code = result.stdout
                    print(code)
                    response = requests.post(token_url, headers=headers, json={
                        "challenge": {
                            "scriptPath": "/scripts/challenge_pow_v1.0.1.js",
                            "payload": payload
                        },
                        "solution": {
                            "payload": code
                        },
                        "action": "auth",
                        "userScope": {}})
                    print(f"🔐 2️⃣ Token попытка #3 — статус: {response.status_code}")
                    print(response.text)
                    try:
                        resp3 = response.json()
                    except json.JSONDecodeError:
                        print("❌ Невалидный JSON (второй ответ):\n")
                        return None
                    secure_token = resp3.get("secureToken")
                    if secure_token:
                        print("✅ secureToken получен после challenge!")
                        print(secure_token)
                        return secure_token
                    else:
                        print("❌ Не удалось получить secureToken после повторной попытки.")
                        print(resp3)
                        return None
        except Exception as e:
            print("Неизвестная ошибка: " + str(e))
            return None





    @staticmethod
    def get_captcha_token():
        get_task_url = "https://pow.wb.ru/api/v1/short/get-task"
        verify_url = "https://pow.wb.ru/api/v1/short/verify-answer"

        response = requests.get(
            url=get_task_url,
            data="wb_supply_code",
            params={"client_id": "client_wb_id"},
        )

        command = ["node", "wasm_exec.js", "solve.wasm", response.text]
        result = subprocess.run(command, capture_output=True, text=True)

        task_answer = json.loads(json.loads(result.stdout))
        verify = requests.post(verify_url, json=task_answer)
        ret = json.loads(verify.text)["wb-captcha-short-token"]
        return ret

    async def send_code(self):
        captcha_token = self.get_secure_token()
        code_url = "https://seller-auth.wildberries.ru/auth/v2/code/wb-captcha"
        payload = {
            "phone_number": self.phone_number,
            "captcha_token": captcha_token
        }
        logger.info("🔐 Запрос кода: %s", payload)
        response = self.session.post(code_url, json=payload)
        logger.info("🔐 Запрос кода: %s %s", response.status_code, response.text)

        if not response.ok:
            return False, "❌ Ошибка запроса кода."

        data = response.json()

        if data.get("result") == 4 and data.get("error") == "waiting resend":
            ttl_seconds = data.get("payload", {}).get("ttl", 0)
            minutes, seconds = divmod(ttl_seconds, 60)
            hours, minutes = divmod(minutes, 60)
            wait_time = f"{hours} ч {minutes} мин" if hours else f"{minutes} мин"
            logger.warning(f"⏳ Превышено количество попыток. Ждите {wait_time}.")
            return False, f"⏳ Вы уже запрашивали код. Попробуйте снова через {wait_time}."

        # Успешный случай
        self.sticker = data.get("payload", {}).get("sticker")
        return True, None

    def authorize(self, code: str):
        auth_url = "https://seller-auth.wildberries.ru/auth/v2/auth"
        payload = {
            "sticker": self.sticker,
            "code": int(code)
        }

        logger.info(f"📡 Авторизация. Код: {code}")
        logger.info(f"📤 Запрос на {auth_url}")
        logger.info(f"📤 Payload: {payload}")

        try:
            response = self.session.post(auth_url, json=payload)
        except Exception as e:
            logger.exception("❌ Ошибка при выполнении запроса авторизации")
            raise Exception("Ошибка подключения к серверу Wildberries") from e

        logger.info(f"📨 Статус ответа: {response.status_code}")
        logger.debug(f"📨 Заголовки ответа: {response.headers}")
        logger.debug(f"📨 Тело ответа (raw): {response.text}")
        logger.debug(f"📥 Cookies после запроса: {self.session.cookies.get_dict()}")

        if not response.ok:
            raise Exception(f"Ошибка запроса авторизации. Статус: {response.status_code}")

        try:
            data = response.json()
        except Exception as e:
            logger.exception("❌ Ошибка при разборе JSON-ответа")
            raise Exception("Невалидный JSON от Wildberries") from e

        logger.info(f"📦 Тип данных ответа: {type(data)}")
        logger.info(f"📦 Ответ JSON: {json.dumps(data, indent=2, ensure_ascii=False)}")

        # Логирование Set-Cookie
        set_cookie_header = response.headers.get("set-cookie")
        logger.info(f"🍪 Set-Cookie: {set_cookie_header}")

        # Достаём wbx-validation-key
        validation_key = None
        if set_cookie_header:
            try:
                cookies_parts = set_cookie_header.split(",")
                for part in cookies_parts:
                    if "wbx-validation-key=" in part:
                        validation_key = part.strip().split(";", 1)[0]
                        logger.info(f"🔑 Найден wbx-validation-key: {validation_key}")
                        break
                else:
                    logger.warning("⚠️ wbx-validation-key не найден в заголовках Set-Cookie.")
            except Exception as e:
                logger.exception("❌ Ошибка при разборе Set-Cookie")

        return {
            "json": data,
            "cookies": self.session.cookies.get_dict(),
            "wbx_validation_key": validation_key,
        }

    async def validate_token(self, token: str, cookie_string: str, session: ClientSession):
        url = "https://seller.wildberries.ru/ns/passport-portal/suppliers-portal-ru/validate"
        headers = self._initialize_headers(cookie_string)
        headers["authorizev3"] = token
        async with session.post(url, headers=headers) as response:
            logger.info(f"Проверка токена: {response.status}")
            return response.status == 200

    async def refresh_token(self, token: str, cookie_string: str, session: ClientSession):
        url = "https://seller.wildberries.ru/upgrade-cookie-authv3"
        headers = self._initialize_headers(cookie_string)
        headers["authorizev3"] = token
        async with session.post(url, headers=headers) as response:
            logger.info(f"Обновление токена: {response.status}")
            if "WBTokenV3" in response.cookies:
                new_token = response.cookies["WBTokenV3"].value
                logger.info(f"Получен новый WBTokenV3: {new_token}")
                return new_token
            else:
                logger.warning("WBTokenV3 не найден в cookies")
                return None

    async def draft_create(self, cookie_string: str, session: ClientSession):
        """
        Создает черновик поставки.

        Args:
            cookie_string (str): Строка с куками.
            session (ClientSession): Асинхронная сессия для HTTP-запросов.

        Returns:
            str: Идентификатор созданного черновика.
        """
        url = "https://seller-supply.wildberries.ru/ns/sm-draft/supply-manager/api/v1/draft/create"
        params = {"params": {}, "jsonrpc": "2.0", "id": self.get_unique_id()}
        headers = self._initialize_headers(cookie_string)
        result = await self._post(url, params, headers, session)
        draft_id = result["result"]["draftID"]
        logger.info(f"Draft created: {draft_id}")
        return draft_id

    async def update_draft(self, draft_id: str, barcodes: list, quantities: list, cookie_string: str, session: ClientSession):
        """
        Обновляет черновик с новыми товарами.

        Args:
            draft_id (str): Идентификатор черновика.
            barcodes (list): Список баркодов.
            quantities (list): Количество товаров для каждого баркода.
            cookie_string (str): Строка с куками.
            session (ClientSession): Асинхронная сессия для HTTP-запросов.

        Returns:
            None
        """
        url = "https://seller-supply.wildberries.ru/ns/sm-draft/supply-manager/api/v1/draft/UpdateDraftGoods"
        goods_updates = [
            {
                "barcode": str(barcode),
                "quantity": quantities[i] if i < len(quantities) else 1,
            }
            for i, barcode in enumerate(barcodes)
        ]

        params = {
            "params": {"draftID": draft_id, "barcodes": goods_updates},
            "jsonrpc": "2.0",
            "id": self.get_unique_id(),
        }
        headers = self._initialize_headers(cookie_string)
        await self._post(url, params, headers, session)
        logger.info("Draft updated successfully.")

    async def supply_create(self, draft_id: str, warehouse_name: str, delivery_name: str, cookie_string: str, session: ClientSession):
        """
        Создает поставку на основе черновика.

        Args:
            draft_id (str): Идентификатор черновика.
            warehouse_name (str): Название склада (ключ для словаря складов).
            delivery_name (str): Тип доставки (ключ для словаря типов доставки).
            cookie_string (str): Строка с куками.
            session (ClientSession): Асинхронная сессия для HTTP-запросов.

        Returns:
            int: Идентификатор созданной поставки (preorder ID).

        Raises:
            ValueError: Если неверный склад или тип поставки.
            Exception: При превышении максимального количества попыток (rate-limit).
        """
        warehouses = Env.get_warehouses()
        delivery_types = Env.get_delivery_types()

        warehouse_id = warehouses.get(warehouse_name)
        delivery_type_id = delivery_types.get(delivery_name)

        if not warehouse_id or not delivery_type_id:
            raise ValueError("Неверный склад или тип поставки")

        url = "https://seller-supply.wildberries.ru/ns/sm-supply/supply-manager/api/v1/supply/create"
        params = {
            "params": {
                "boxTypeMask": delivery_type_id,
                "draftID": draft_id,
                "transitWarehouseId": None,
                "warehouseId": warehouse_id,
            },
            "jsonrpc": "2.0",
            "id": self.get_unique_id(),
        }
        headers = self._initialize_headers(cookie_string)

        max_retries = 5  # Максимальное количество попыток
        base_delay = 5  # Базовая задержка в секундах

        for attempt in range(max_retries):
            try:
                result = await self._post(url, params, headers, session)
                if (
                        "result" not in result
                        or "ids" not in result["result"]
                        or not result["result"]["ids"]
                ):
                    raise ValueError("Server response is missing required fields.")

                preorder_id = result["result"]["ids"][0]["Id"]
                logger.info(f"Supply created with preorder ID: {preorder_id}")
                return preorder_id

            except ClientResponseError as e:
                if e.status == 429:
                    delay = base_delay * (2 ** attempt)  # Экспоненциальная задержка
                    logger.warning(
                        f"Rate limit exceeded. Retrying in {delay} seconds..."
                    )
                    await asyncio.sleep(delay)
                else:
                    raise
            except Exception as e:
                logger.error(f"An error occurred: {e}")
                raise

        raise Exception("Max retries exceeded. Failed to create supply.")

    async def fetch_acceptance_costs(self, supply_id: int, cookie_string: str, session: ClientSession):
        """
        Получает коэффициенты приемки для одного supply_id.

        Args:
            supply_id (int): Идентификатор поставки.
            cookie_string (str): Строка с куками.
            session (ClientSession): Сессия для выполнения запросов.

        Returns:
            dict | int: Результат в формате JSON или 429, если Too Many Requests.

        Raises:
            Exception: В случае ошибки, отличной от 429.
        """
        url = "https://seller-supply.wildberries.ru/ns/sm-supply/supply-manager/api/v1/supply/getAcceptanceCosts"
        cookies = {
            cookie.split("=")[0]: cookie.split("=")[1]
            for cookie in cookie_string.split("; ")
        }
        date_from = (datetime.now() - timedelta(days=1)).strftime(
            "%Y-%m-%dT%H:%M:%S.%f"
        )[:-3] + "Z"
        date_to = (datetime.now() + timedelta(days=30)).strftime(
            "%Y-%m-%dT%H:%M:%S.%f"
        )[:-3] + "Z"

        payload = {
            "params": {
                "dateFrom": date_from,
                "dateTo": date_to,
                "preorderID": int(supply_id),
            },
            "jsonrpc": "2.0",
            "id": f"json-rpc_{random.randint(1, 999)}",
        }

        headers = self._initialize_headers(cookie_string)
        async with session.post(
                url, json=payload, headers=headers, cookies=cookies
        ) as response:
            if response.status == 429:
                logger.warning("Получен статус 429 Too Many Requests")
                return 429
            response.raise_for_status()
            return await response.json()

    async def create_supply(self, barcodes: list, quantities: list, warehouse_name: str, delivery_name: str, cookie_string: str, session: ClientSession):
        """
        Создает поставку:
        1) Черновик,
        2) Обновление черновика (товары),
        3) Создание поставки (preorder).

        Args:
            barcodes (list): Список баркодов (строк или чисел).
            quantities (list): Список количеств товаров (соответствуют barcodes по индексу).
            warehouse_name (str): Название склада (ключ в Env.get_warehouses()).
            delivery_name (str): Тип доставки (ключ в Env.get_delivery_types()).
            cookie_string (str): Строка с куками.
            session (ClientSession): Асинхронная сессия.

        Returns:
            int: Идентификатор созданной поставки (preorder ID).

        Raises:
            Exception: В случае неудачных попыток или неизвестной ошибки.
        """
        # Убедимся, что баркоды — строки
        barcodes = [str(barcode) for barcode in barcodes]

        logger.info(f"Создание поставки со списком баркодов: {barcodes}")

        max_retries = 3  # Максимальное количество попыток при 429 ошибке
        retry_delay = 5  # Задержка в секундах перед повторной попыткой

        for attempt in range(max_retries):
            try:
                draft_id = await self.draft_create(cookie_string, session)
                logger.info(f"Создан черновик поставки с ID: {draft_id}")
                await asyncio.sleep(5)
                await self.update_draft(
                    draft_id, barcodes, quantities, cookie_string, session
                )
                logger.info(f"Черновик обновлён: {draft_id}")
                await asyncio.sleep(5)
                preorder_id = await self.supply_create(
                    draft_id, warehouse_name, delivery_name, cookie_string, session
                )
                logger.info(f"Поставка создана (preorder ID): {preorder_id}")

                return preorder_id

            except ClientResponseError as e:
                if e.status == 429:
                    logger.warning(
                        f"Получена ошибка 429 (слишком много запросов). "
                        f"Попытка {attempt + 1} из {max_retries}. "
                        f"Повтор через {retry_delay} секунд..."
                    )
                    await asyncio.sleep(retry_delay)
                else:
                    logger.error(f"Ошибка при создании поставки: {e}")
                    raise
            except Exception as e:
                logger.error(f"Неожиданная ошибка при создании поставки: {e}")
                raise

        logger.error(f"Не удалось создать поставку после {max_retries} попыток.")
        raise Exception(
            "Превышено максимальное количество попыток при создании поставки."
        )

    async def supply_details(self, supply_id: int, cookie_string: str, session: ClientSession):
        """
        Получает детали поставки по её ID.

        Args:
            supply_id (int): Идентификатор поставки.
            cookie_string (str): Строка с куками.
            session (ClientSession): Асинхронная сессия.

        Returns:
            dict | int: Детали поставки или код 429 при превышении лимита запросов.
        """
        url = "https://seller-supply.wildberries.ru/ns/sm-supply/supply-manager/api/v1/supply/supplyDetails"
        supply_id_str = str(supply_id)  # Преобразуем в строку для проверки
        payload = {
            "params": {"pageNumber": 1, "pageSize": 100, "search": ""},
            "jsonrpc": "2.0",
            "id": self.get_unique_id(),
        }
        if supply_id_str.startswith("2"):
            payload["params"]["supplyID"] = int(supply_id_str)
        else:
            payload["params"]["preorderID"] = int(supply_id_str)

        headers = self._initialize_headers(cookie_string)

        try:
            result = await self._post(url, payload, headers, session)
            logger.info(f"Детали поставки получены для supply_id: {supply_id}")
            return result
        except ClientResponseError as e:
            if 400 <= e.status < 500:
                logger.warning(f"Получен статус {e.status}")
                return e.status
            else:
                logger.error(f"Ошибка при получении деталей поставки: {e}")
                raise
        except Exception as e:
            logger.error(f"Неожиданная ошибка при получении деталей поставки: {e}")
            raise

    async def add(self, preorder_id: int, delivery_date: str, token: str, is_pallet: bool, cookie_string: str, session: ClientSession):
        """Submit a delivery date to the API."""
        url = (
            "https://seller-supply.wildberries.ru/ns/sm/supply-manager/api/v1/plan/add"
        )
        payload = {
            "params": {
                "preOrderId": int(preorder_id),
                "deliveryDate": f"{delivery_date}",
            },
            "jsonrpc": "2.0",
            "id": "json-rpc_" + self.get_unique_id(),
        }
        if str(payload["params"]["preOrderId"])[0] == "2":
            payload["params"]["supplyID"] = int(payload["params"]["preOrderId"])
            payload["params"].pop("preOrderId")
            url = "https://seller-supply.wildberries.ru/ns/sm/supply-manager/api/v1/plan/update"
        elif is_pallet:
            payload["params"]["monopalletCount"] = 1
        headers = self._initialize_headers(cookie_string)
        headers["x-wb-captcha-token"] = token
        response = await self._post(url, payload, headers, session)
        logging.debug(
            f"Дата доставки отправлена с кодом ответа {response['id']}, ID: {preorder_id}"
        )
        headers.pop("x-wb-captcha-token")
        logging.debug(f"Ответ для ID {preorder_id}: {response}")
        return response

    async def delete_supply(self, preorder_id: int, cookie_string: str, session: ClientSession):
        """
        Удаляет поставку по её ID.
        """
        url = "https://seller-supply.wildberries.ru/ns/sm-preorder/supply-manager/api/v1/preorder/delete"
        payload = {
            "params": {"preorderId": preorder_id},
            "jsonrpc": "2.0",
            "id": self.get_unique_id(),
        }
        headers = self._initialize_headers(cookie_string)

        try:
            response = await self._post(url, payload, headers, session)
            logger.info(f"Поставка {preorder_id} успешно удалена.")
            return response
        except Exception as e:
            logger.error(f"Ошибка при удалении поставки {preorder_id}: {e}")
            raise

    async def get_suppliers(self, cookie_string: str, session: ClientSession):
        url = "https://seller.wildberries.ru/ns/suppliers/suppliers-portal-core/suppliers"
        headers = self._initialize_headers(cookie_string)
        payload = [{
            "method": "getUserSuppliers",
            "params": {},
            "id": self.get_unique_id(),
            "jsonrpc": "2.0"
        }]

        logger.info("📡 Получение списка поставщиков")
        logger.debug(f"📤 Headers: {headers}")
        logger.debug(f"📤 Cookies: {self.parse_cookies(cookie_string)}")
        logger.debug(f"📤 Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")

        try:
            async with session.post(url, headers=headers, cookies=self.parse_cookies(cookie_string),
                                    json=payload) as response:
                logger.info(f"📨 Статус ответа: {response.status}")
                response.raise_for_status()
                result = await response.json()
                logger.debug(f"📦 Ответ от API: {json.dumps(result, indent=2, ensure_ascii=False)}")
                return result
        except Exception as e:
            logger.exception("❌ Ошибка при получении поставщиков")
            raise


