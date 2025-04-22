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
    async def get_secure_token() -> str | None:
        """
        Получает one-time-token с antibot.wildberries.ru (x-wb-captcha-token).
        Используется при планировании поставки.
        """
        url = "https://antibot.wildberries.ru/api/v1/create-one-time-token"
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Content-Type": "application/json",
            "Accept": "*/*",
        }

        async with aiohttp.ClientSession() as session:
            try:
                # Первый запрос — без payload
                payload1 = {
                    "action": "ADD_OR_UPDATE_SUPPLY",
                    "challenge": {},
                    "userScope": {}
                }
                async with session.post(url, headers=headers, json=payload1) as r:
                    raw = await r.text()
                    logger.info(f"🔐 Token запрос #1 — статус: {r.status}")
                    resp = json.loads(raw)

                    if r.status == 200 and "secureToken" in resp:
                        logger.info("✅ secureToken получен с первой попытки")
                        return resp["secureToken"]

                    # Challenge
                    if resp.get("code") == 498 and "challenge" in resp:
                        challenge_payload = resp["challenge"].get("payload")
                        if not challenge_payload:
                            logger.warning("⚠️ Challenge без payload — прервано.")
                            return None

                        payload2 = {
                            "action": "ADD_OR_UPDATE_SUPPLY",
                            "challenge": {
                                "scriptPath": "/scripts/challenge_fingerprint_v1.0.3.js",
                                "payload": challenge_payload,
                            },
                            "solution": {
                                "payload": Env.get_antibot_solution()
                            },
                            "userScope": {}
                        }

                        async with session.post(url, headers=headers, json=payload2) as r2:
                            raw2 = await r2.text()
                            logger.info(f"🔐 Token запрос #2 — статус: {r2.status}")
                            resp2 = json.loads(raw2)

                            token = resp2.get("secureToken")
                            if token:
                                logger.info("✅ secureToken получен после challenge")
                                return token
                            else:
                                logger.warning("❌ Token не получен во втором запросе")
                                return None
            except Exception as e:
                logger.exception("❌ Ошибка при получении secureToken")
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

    def send_code(self):
        captcha_token = self.get_secure_token()
        code_url = "https://seller-auth.wildberries.ru/auth/v2/code/wb-captcha"
        payload = {
            "phone_number": self.phone_number,
            "captcha_token": captcha_token
        }
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


