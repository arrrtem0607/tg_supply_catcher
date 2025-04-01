import logging
import aiohttp
import uuid

logger = logging.getLogger(__name__)

STATUS_TRANSLATION = {
    "RECEIVED": "📥 Получено",
    "CATCHING": "🎯 Ловится",
    "CAUGHT": "✅ Поймано",
    "ERROR": "❌ Ошибка",
    "CANCELLED": "🚫 Отменено",
    "PLANNED": "📌 Запланировано",
    "IN_PROGRESS": "⏳ В процессе",
    "COMPLETED": "✅ Завершено",
}

class MPWAVEAPI:
    BASE_URL = "http://127.0.0.1:8001"

    @staticmethod
    async def register_user_api(tg_id: int):
        url = f"{MPWAVEAPI.BASE_URL}/catcher/register/user"
        async with aiohttp.ClientSession() as client:
            try:
                logger.debug(f"🔄 POST {url} | params={{'tg_id': {tg_id}}}")
                async with client.post(url, params={"tg_id": tg_id}) as response:
                    logger.debug(f"✅ Ответ {response.status} на register_user_api")
                    return response
            except Exception as e:
                logger.error(f"❌ Ошибка в register_user_api: {e}", exc_info=True)
                return None

    @staticmethod
    async def register_client_api(tg_id: int, client_id: str, name: str, cookies: str) -> dict:
        url = f"{MPWAVEAPI.BASE_URL}/catcher/register/client"
        async with aiohttp.ClientSession() as session:
            try:
                logger.debug(f"🔄 POST {url} | data={{'tg_id': {tg_id}, 'name': '{name}'}}")
                response = await session.post(
                    url,
                    params={"user_id": tg_id,
                            "client_id": client_id,
                            "name": name,
                            "cookies": cookies},
                    timeout=10,
                )
                response.raise_for_status()
                json_data = await response.json()
                logger.debug(f"✅ Ответ 200: {json_data}")
                return json_data
            except aiohttp.ClientResponseError as e:
                error_text = await response.text()
                logger.error(f"❌ Ошибка клиента: {e.status} {e.message}. Ответ сервера: {error_text}")
                return {"error": f"Ошибка сервера: {e.status} {e.message}"}
            except Exception as e:
                logger.error(f"❌ Ошибка соединения: {e}", exc_info=True)
                return {"error": f"Ошибка соединения: {str(e)}"}

    @staticmethod
    async def update_client_name_api(client_id: str, name: str):
        url = f"{MPWAVEAPI.BASE_URL}/catcher/set_name"
        async with aiohttp.ClientSession() as http:
            try:
                logger.debug(f"🔄 POST {url} | data={{'client_id': '{client_id}', 'name': '{name}'}}")
                response = await http.post(url, json={"client_id": client_id, "name": name})
                logger.debug(f"✅ Ответ {response.status} на update_client_name_api")
                return response
            except Exception as e:
                logger.error(f"❌ Ошибка в update_client_name_api: {e}", exc_info=True)
                return None

    @staticmethod
    async def update_client_cookies_api(client_id: str, cookies: str):
        url = f"{MPWAVEAPI.BASE_URL}/catcher/set_cookies"
        async with aiohttp.ClientSession() as http:
            try:
                logger.debug(f"🔄 POST {url} | data={{'client_id': '{client_id}', 'cookies': '[HIDDEN]'}}")
                response = await http.post(url, json={"client_id": client_id, "cookies": cookies})
                logger.debug(f"✅ Ответ {response.status} на update_client_cookies_api")
                return response
            except Exception as e:
                logger.error(f"❌ Ошибка в update_client_cookies_api: {e}", exc_info=True)
                return None

    @staticmethod
    async def cancel_task_api(client_id: str, preorder_id: int):
        url = f"{MPWAVEAPI.BASE_URL}/catcher/cancel_task"
        async with aiohttp.ClientSession() as session_http:
            try:
                logger.debug(f"🔄 POST {url} | data={{'client_id': '{client_id}', 'preorder_id': {preorder_id}}}")
                response = await session_http.post(url, json={"client_id": client_id, "preorder_id": preorder_id})
                logger.debug(f"✅ Ответ {response.status} на cancel_task_api")
                return response
            except Exception as e:
                logger.error(f"❌ Ошибка в cancel_task_api: {e}", exc_info=True)
                return None

    @staticmethod
    async def start_task_api(data: dict):
        url = f"{MPWAVEAPI.BASE_URL}/catcher/start_task"
        async with aiohttp.ClientSession() as client:
            try:
                logger.debug(f"🔄 Отправка запроса POST {url} | data={data}")
                response = await client.post(url, json=data)
                response_text = await response.text()

                if response.status == 200:
                    logger.debug(f"✅ Успешный ответ от start_task_api: {response_text}")
                else:
                    logger.warning(f"⚠️ Ответ {response.status} от start_task_api: {response_text}")

                return response
            except aiohttp.ClientResponseError as e:
                logger.error(f"❌ ClientResponseError {e.status} в start_task_api: {e.message}", exc_info=True)
                return None
            except Exception as e:
                logger.error(f"❌ Ошибка в start_task_api: {e}", exc_info=True)
                return None

    @staticmethod
    async def fetch_supplies_from_api(client_id: str):
        url = f"{MPWAVEAPI.BASE_URL}/catcher/all_supplies"
        params = {"client_id": client_id}

        async with aiohttp.ClientSession() as http_session:
            try:
                logger.debug(f"🔄 GET {url} | params={params}")
                async with http_session.get(url, params=params) as response:
                    response_text = await response.text()
                    if response.status != 200:
                        logger.error(f"❌ Ошибка API {response.status}: {response_text}")
                        return None, f"Ошибка API: {response.status}, Ответ: {response_text}"
                    json_data = await response.json()
                    logger.debug(f"✅ Успешный ответ от API: {json_data}")
                    return json_data, None
            except Exception as e:
                logger.error(f"❌ Ошибка запроса к API: {e}", exc_info=True)
                return None, f"Ошибка запроса к API: {e}"
