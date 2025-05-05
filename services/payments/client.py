import aiohttp
from typing import Optional, List
from configurations.payments_config import PaymentsConfig

class TochkaAPIClient:
    BASE_URL = "https://enter.tochka.com/uapi"
    API_VERSION = "v1.0"

    def __init__(self, config: PaymentsConfig):
        self.jwt = config.get_jwt_token()
        self.customer_code = config.get_customer_code()
        self.headers = {
            "Authorization": f"Bearer {self.jwt}",
            "Content-Type": "application/json"
        }

    async def create_payment_link(self, payload: dict) -> str:
        url = f"{self.BASE_URL}/acquiring/{self.API_VERSION}/payments"
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.post(url, json={"Data": payload}) as resp:
                if resp.status != 200:
                    print("❌ Ошибка при создании ссылки:")
                    print("Status:", resp.status)
                    print("Response:", await resp.text())
                    resp.raise_for_status()
                data = await resp.json()
                return data["Data"]["paymentLink"]

    async def create_payment_link_with_receipt(self, payload: dict) -> str:
        url = f"{self.BASE_URL}/acquiring/{self.API_VERSION}/payments_with_receipt"
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.post(url, json={"Data": payload}) as resp:
                resp.raise_for_status()
                data = await resp.json()
                return data["Data"]["paymentLink"]

    async def get_payment_status(self, operation_id: str) -> Optional[str]:
        url = f"{self.BASE_URL}/acquiring/{self.API_VERSION}/payments/{operation_id}"
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.get(url) as resp:
                resp.raise_for_status()
                data = await resp.json()
                ops = data.get("Data", {}).get("Operation", [])
                return ops[0].get("status") if ops else None

    async def list_payment_operations(
        self,
        from_date: str,
        to_date: str,
        status: Optional[str] = None,
        page: int = 1,
        per_page: int = 1000
    ) -> List[dict]:
        params = {
            "customerCode": self.customer_code,
            "fromDate": from_date,
            "toDate": to_date,
            "page": page,
            "perPage": per_page,
        }
        if status:
            params["status"] = status

        url = f"{self.BASE_URL}/acquiring/{self.API_VERSION}/payments"
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.get(url, params=params) as resp:
                resp.raise_for_status()
                data = await resp.json()
                return data.get("Data", {}).get("Operation", [])

    async def refund_payment(self, operation_id: str, amount: float) -> bool:
        url = f"{self.BASE_URL}/acquiring/{self.API_VERSION}/payments/{operation_id}/refund"
        payload = {"Data": {"amount": f"{amount:.2f}"}}
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.post(url, json=payload) as resp:
                resp.raise_for_status()
                data = await resp.json()
                return data["Data"].get("isRefund", False)

    async def get_retailers(self) -> List[dict]:
        url = f"{self.BASE_URL}/acquiring/{self.API_VERSION}/retailers"
        params = {"customerCode": self.customer_code}
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.get(url, params=params) as resp:
                resp.raise_for_status()
                data = await resp.json()
                return data.get("Data", {}).get("Retailer", [])

    async def get_customers(self) -> List[dict]:
        url = f"{self.BASE_URL}/open-banking/{self.API_VERSION}/customers"
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.get(url) as resp:
                resp.raise_for_status()
                data = await resp.json()
                return data.get("Data", {}).get("Customer", [])

    async def create_webhook(self, url: str, events: list[str]) -> dict:
        client_id = PaymentsConfig().get_client_id()
        endpoint = f"{self.BASE_URL}/webhook/{self.API_VERSION}/{client_id}"
        payload = {"webhooksList": events, "url": url}
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.put(endpoint, json=payload) as resp:
                resp.raise_for_status()
                return await resp.json()

    async def edit_webhook(self, url: str, events: list[str]) -> dict:
        client_id = PaymentsConfig().get_client_id()
        endpoint = f"{self.BASE_URL}/webhook/{self.API_VERSION}/{client_id}"
        payload = {"webhooksList": events, "url": url}
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.post(endpoint, json=payload) as resp:
                resp.raise_for_status()
                return await resp.json()

    async def get_webhooks(self) -> dict:
        client_id = PaymentsConfig().get_client_id()
        endpoint = f"{self.BASE_URL}/webhook/{self.API_VERSION}/{client_id}"
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.get(endpoint) as resp:
                resp.raise_for_status()
                return await resp.json()

    async def delete_webhook(self) -> dict:
        client_id = PaymentsConfig().get_client_id()
        endpoint = f"{self.BASE_URL}/webhook/{self.API_VERSION}/{client_id}"
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.delete(endpoint) as resp:
                resp.raise_for_status()
                return await resp.json()

    async def test_webhook(self, webhook_type: str) -> dict:
        client_id = PaymentsConfig().get_client_id()
        endpoint = f"{self.BASE_URL}/webhook/{self.API_VERSION}/{client_id}/test_send"
        payload = {"webhookType": webhook_type}
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.post(endpoint, json=payload) as resp:
                resp.raise_for_status()
                return await resp.json()

    async def setup_webhook(self, url: str):
        client_id = PaymentsConfig().get_client_id()
        endpoint = f"{self.BASE_URL}/webhook/{self.API_VERSION}/{client_id}"
        payload = {
            "webhooksList": ["acquiringInternetPayment"],
            "url": url
        }
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.put(endpoint, json=payload) as resp:
                resp.raise_for_status()
                return await resp.json()


async def get_retailers_safe(client: TochkaAPIClient):
    print("➡️ Получаем список торговых точек через API...")
    try:
        retailers = await client.get_retailers()
        if not retailers:
            print("⚠️ Торговые точки не найдены.")
            return
        for i, r in enumerate(retailers):
            print(f"\n🔹 Торговая точка #{i+1}:")
            print("name:", r.get("name"))
            print("merchantId:", r.get("merchantId"))
            print("customerCode:", r.get("customerCode"))
            print("isActive:", r.get("isActive"))
            print("status:", r.get("status"))
    except aiohttp.ClientResponseError as e:
        print(f"❌ Ошибка {e.status}: {e.message}")
        if e.status == 403:
            print("🔒 Проверь, есть ли у токена разрешение ReadAcquiringData")
        elif e.status == 400:
            print("❗ Вероятно, указан неверный customerCode")
        elif e.status == 501:
            print("❌ Метод не поддерживается. Обратись в поддержку Точки.")
        else:
            raise
