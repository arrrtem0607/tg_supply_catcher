import asyncio
import functools
import re
import subprocess
from datetime import datetime, timedelta

import requests
from aiohttp import ClientResponseError, ClientSession

from configurations.reading_env import Env
from services.utils.logger import setup_logger

logger = setup_logger(__name__)

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
    def __init__(self, proxy_manager=None):
        self.proxy_manager = proxy_manager
        self.json_rpc_number = 1
        self.sticker = None

    @staticmethod
    def _initialize_headers(cookie_string: str):
        return {
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

    def get_unique_id(self):
        uid = f"json-rpc_{self.json_rpc_number}"
        self.json_rpc_number += 1
        return uid

    @use_proxy
    async def _post(self, url: str, json: dict, headers: dict, session: ClientSession, proxy_url=None):
        try:
            async with session.post(url, json=json, headers=headers, proxy=proxy_url) as response:
                response.raise_for_status()
                return await response.json()
        except Exception as e:
            logger.error(f"Ошибка POST-запроса: {e}")
            raise

    @staticmethod
    def parse_cookies(cookie_str):
        return dict(item.strip().split("=", 1) for item in cookie_str.split(";") if "=" in item)

    @staticmethod
    def assemble_cookie(wb_token: str, validation_key: str, supplier_id: str) -> str:
        """
        Собирает строку cookies из трёх компонентов, необходимых для авторизации на WB.
        """
        return f"WBTokenV3={wb_token}; wbx-validation-key={validation_key}; x-supplier-id={supplier_id}"

    @staticmethod
    def get_secure_token():
        try:
            token_url = "https://antibot.wildberries.ru/api/v1/create-one-time-token"
            headers = {
                "User-Agent": "Mozilla/5.0",
                "Accept": "*/*",
                "Content-Type": "application/json",
                "X-WB-Antibot-Key": "217cc4d5276448d6a980d07034a3c89c",
                "X-WB-Antibot-SDK-Version": "1.0.0",
            }
            r = requests.post(token_url, headers=headers, json={"action": "auth", "challenge": {}, "userScope": {}})
            resp = r.json()
            if resp.get("code") == 498 and "challenge" in resp:
                payload = resp["challenge"].get("payload")
                if not payload:
                    return None
                command = ["node", 'starter.js', payload]
                result = subprocess.run(command, capture_output=True, text=True)
                code = result.stdout
                r2 = requests.post(token_url, headers=headers, json={
                    "challenge": {"scriptPath": "/scripts/challenge_pow_v1.0.1.js", "payload": payload},
                    "solution": {"payload": code},
                    "action": "auth",
                    "userScope": {}
                })
                return r2.json().get("secureToken")
            return resp.get("secureToken")
        except Exception as e:
            logger.error(f"get_secure_token error: {e}")
            return None

    def send_code(self, phone_number: str):
        token = self.get_secure_token()
        url = "https://seller-auth.wildberries.ru/auth/v2/code/wb-captcha"
        payload = {"phone_number": phone_number, "captcha_token": token}
        r = requests.post(url, json=payload)
        if not r.ok:
            return False, r.text
        data = r.json()
        self.sticker = data.get("payload", {}).get("sticker")
        return True, None

    def authorize(self, code: str):
        url = "https://seller-auth.wildberries.ru/auth/v2/auth"
        payload = {"sticker": self.sticker, "code": int(code)}
        r = requests.post(url, json=payload)
        return r.json(), r.cookies.get_dict(), r.headers.get("set-cookie")

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

    async def get_suppliers(self, cookie_string: str, session: ClientSession):
        url = "https://seller.wildberries.ru/ns/suppliers/suppliers-portal-core/suppliers"
        headers = self._initialize_headers(cookie_string)
        payload = [{
            "method": "getUserSuppliers",
            "params": {},
            "id": self.get_unique_id(),
            "jsonrpc": "2.0"
        }]
        try:
            async with session.post(url, headers=headers, cookies=self.parse_cookies(cookie_string), json=payload) as response:
                logger.info(f"📨 Статус ответа: {response.status}")
                response.raise_for_status()
                return await response.json()
        except Exception as e:
            logger.exception("❌ Ошибка при получении поставщиков")
            raise

    async def draft_create(self, cookie_string: str, session: ClientSession):
        url = "https://seller-supply.wildberries.ru/ns/sm-draft/supply-manager/api/v1/draft/create"
        params = {"params": {}, "jsonrpc": "2.0", "id": self.get_unique_id()}
        headers = self._initialize_headers(cookie_string)
        result = await self._post(url, params, headers, session)
        return result["result"]["draftID"]

    async def update_draft(self, draft_id: str, barcodes: list, quantities: list, cookie_string: str, session: ClientSession):
        url = "https://seller-supply.wildberries.ru/ns/sm-draft/supply-manager/api/v1/draft/UpdateDraftGoods"
        goods_updates = [
            {"barcode": str(barcode), "quantity": quantities[i] if i < len(quantities) else 1}
            for i, barcode in enumerate(barcodes)
        ]
        params = {
            "params": {"draftID": draft_id, "barcodes": goods_updates},
            "jsonrpc": "2.0",
            "id": self.get_unique_id(),
        }
        headers = self._initialize_headers(cookie_string)
        await self._post(url, params, headers, session)

    async def supply_create(self, draft_id: str, warehouse_name: str, delivery_name: str, cookie_string: str, session: ClientSession):
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
        for attempt in range(5):
            try:
                result = await self._post(url, params, headers, session)
                preorder_id = result["result"]["ids"][0]["Id"]
                return preorder_id
            except ClientResponseError as e:
                if e.status == 429:
                    await asyncio.sleep(5 * (2 ** attempt))
                else:
                    raise
        raise Exception("Max retries exceeded")

    async def fetch_acceptance_costs(self, supply_id: int, cookie_string: str, session: ClientSession):
        url = "https://seller-supply.wildberries.ru/ns/sm-supply/supply-manager/api/v1/supply/getAcceptanceCosts"
        cookies = self.parse_cookies(cookie_string)
        date_from = (datetime.now() - timedelta(days=1)).isoformat() + "Z"
        date_to = (datetime.now() + timedelta(days=30)).isoformat() + "Z"
        payload = {
            "params": {"dateFrom": date_from, "dateTo": date_to, "preorderID": int(supply_id)},
            "jsonrpc": "2.0",
            "id": self.get_unique_id(),
        }
        headers = self._initialize_headers(cookie_string)
        async with session.post(url, json=payload, headers=headers, cookies=cookies) as response:
            if response.status == 429:
                return 429
            response.raise_for_status()
            return await response.json()

    async def create_supply(self, barcodes: list, quantities: list, warehouse_name: str, delivery_name: str, cookie_string: str, session: ClientSession):
        barcodes = [str(b) for b in barcodes]
        for attempt in range(3):
            try:
                draft_id = await self.draft_create(cookie_string, session)
                await asyncio.sleep(2)
                await self.update_draft(draft_id, barcodes, quantities, cookie_string, session)
                await asyncio.sleep(2)
                preorder_id = await self.supply_create(draft_id, warehouse_name, delivery_name, cookie_string, session)
                return preorder_id
            except ClientResponseError as e:
                if e.status == 429:
                    await asyncio.sleep(5)
                else:
                    raise
        raise Exception("Не удалось создать поставку после 3 попыток")

    async def supply_details(self, supply_id: int, cookie_string: str, session: ClientSession):
        url = "https://seller-supply.wildberries.ru/ns/sm-supply/supply-manager/api/v1/supply/supplyDetails"
        payload = {
            "params": {"pageNumber": 1, "pageSize": 100, "search": ""},
            "jsonrpc": "2.0",
            "id": self.get_unique_id(),
        }
        sid = str(supply_id)
        if sid.startswith("2"):
            payload["params"]["supplyID"] = int(sid)
        else:
            payload["params"]["preorderID"] = int(sid)
        headers = self._initialize_headers(cookie_string)
        try:
            return await self._post(url, payload, headers, session)
        except ClientResponseError as e:
            if 400 <= e.status < 500:
                return e.status
            raise

    async def add(self, preorder_id: int, delivery_date: str, token: str, is_pallet: bool, cookie_string: str, session: ClientSession):
        url = "https://seller-supply.wildberries.ru/ns/sm/supply-manager/api/v1/plan/add"
        payload = {
            "params": {
                "preOrderId": int(preorder_id),
                "deliveryDate": delivery_date,
            },
            "jsonrpc": "2.0",
            "id": self.get_unique_id(),
        }
        if str(preorder_id).startswith("2"):
            payload["params"]["supplyID"] = preorder_id
            payload["params"].pop("preOrderId")
            url = "https://seller-supply.wildberries.ru/ns/sm/supply-manager/api/v1/plan/update"
        elif is_pallet:
            payload["params"]["monopalletCount"] = 1
        headers = self._initialize_headers(cookie_string)
        headers["x-wb-captcha-token"] = token
        response = await self._post(url, payload, headers, session)
        headers.pop("x-wb-captcha-token")
        return response

    async def delete_supply(self, preorder_id: int, cookie_string: str, session: ClientSession):
        url = "https://seller-supply.wildberries.ru/ns/sm-preorder/supply-manager/api/v1/preorder/delete"
        payload = {
            "params": {"preorderId": preorder_id},
            "jsonrpc": "2.0",
            "id": self.get_unique_id(),
        }
        headers = self._initialize_headers(cookie_string)
        return await self._post(url, payload, headers, session)

    async def validate_cookie(self, cookie_str):
        headers = self._initialize_headers(cookie_str)
        url = "https://seller.wildberries.ru/ns/passport-portal/suppliers-portal-ru/validate"
        try:
            response = requests.post(url, headers=headers)
            status = response.status_code
            print(f"Валидно: {'Да' if status == 200 else 'Нет'}")
            if status != 200:
                return False
            else:
                return True
        except Exception as e:
            print(f"Ошибка запроса: {e}")
            return False

    async def update_cookie(self, cookie_str, refresh_token):
        headers = self._initialize_headers(cookie_str + " ; wbx-refresh=" + refresh_token)
        url = "https://seller-auth.wildberries.ru/auth/v2/auth/slide-v3"
        response = requests.post(url, headers=headers)
        print(f"📨 Status: {response.status_code}")
        print("📨 Headers:")
        print(response.headers)
        refresh = None
        for k, v in response.headers.items():
            if "wbx-refresh" in v:
                cookies_parts = re.split(r'[;,]\s*', v)
                for part in cookies_parts:
                    if "wbx-refresh" in part:
                        refresh = part.split("=")[1]
        tokenv3 = None
        print(response.text)
        try:
            ans = response.json()
            tokenv3 = ans['payload']['access_token']
        except Exception as e:
            print("Ошибка запроса(Невалидный json)")
            return None
        print(f"🍪 Set-Cookie refresh: {refresh}")
        print(f"🍪 Set-Cookie v3: {tokenv3}")
        return {"tokenv3": tokenv3, "refresh": refresh}

