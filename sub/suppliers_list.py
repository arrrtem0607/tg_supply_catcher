import requests
import json

# URL запроса
url = "https://seller.wildberries.ru/ns/suppliers/suppliers-portal-core/suppliers"

# Авторизационный токен (замени на актуальный)
WBTokenV3 = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE3NDMzMTkxMTksInZlcnNpb24iOjIsInVzZXIiOiIyODcyMDE1MiIsInNoYXJkX2tleSI6IjIiLCJjbGllbnRfaWQiOiJzZWxsZXItcG9ydGFsIiwic2Vzc2lvbl9pZCI6IjhiMjM3MzY0OWQwMjQxYzViMmQ5YjhjN2I3ZDcwYjkwIiwidXNlcl9yZWdpc3RyYXRpb25fZHQiOjE2NzQwNzA3MDYsInZhbGlkYXRpb25fa2V5IjoiZjRjZDMxMzc4MTMyZjkwOTBkZjFjNmRlNzUwOTk3NTQ3MjgzOGU3Mjc5MWQ5ODYxYTdiZDllOGEyMjZkMWZhYiJ9.qJc15cOnJ_2IZ1nqeLdTzcw0PjRM9D64xh7SYhyIyX--RxdbxXyoINFiPCzUhfnZWZko-1WrDzaBmgIhuXObleNcz7m5bacO09niqYcNAy8S1Ai2RwhnHl_tWCgwXDTtBDRnawEU9XxLHUdfjHNPAwRT2-ec7kn2mzO4D2x3hZPqJsEH2zlHPKoW6-PfXo_6Wh65gnwZjowpS7vZconh5BpX31D4WmiP6hTwc27keS_MBI6ZVlVIk-pZhgytq3GRTbdcNLwqtfOfCiNGoqElIbSLlyvnb7FfnNtjWub3eyY9lCdgmLDqVh-POBbDVEZMz7WrD77WrOSvXXkfsC-t1Q"

# Заголовки
headers = {
    "accept": "*/*",
    "content-type": "application/json",
    "origin": "https://seller.wildberries.ru",
    "referer": "https://seller.wildberries.ru/",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)...",
    "authorizev3": WBTokenV3,
}

# Парсинг cookies
def parse_cookies(cookie_str):
    cookies = {}
    for item in cookie_str.split(";"):
        if "=" in item:
            key, value = item.strip().split("=", 1)
            cookies[key] = value
    return cookies

# Вставь свои куки ниже
cookie_string = "wbx-validation-key=6fd98b2d-8c50-441a-8bc0-aecd77055cb7;WBTokenV3=eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE3NDMzMTkxMTksInZlcnNpb24iOjIsInVzZXIiOiIyODcyMDE1MiIsInNoYXJkX2tleSI6IjIiLCJjbGllbnRfaWQiOiJzZWxsZXItcG9ydGFsIiwic2Vzc2lvbl9pZCI6IjhiMjM3MzY0OWQwMjQxYzViMmQ5YjhjN2I3ZDcwYjkwIiwidXNlcl9yZWdpc3RyYXRpb25fZHQiOjE2NzQwNzA3MDYsInZhbGlkYXRpb25fa2V5IjoiZjRjZDMxMzc4MTMyZjkwOTBkZjFjNmRlNzUwOTk3NTQ3MjgzOGU3Mjc5MWQ5ODYxYTdiZDllOGEyMjZkMWZhYiJ9.qJc15cOnJ_2IZ1nqeLdTzcw0PjRM9D64xh7SYhyIyX--RxdbxXyoINFiPCzUhfnZWZko-1WrDzaBmgIhuXObleNcz7m5bacO09niqYcNAy8S1Ai2RwhnHl_tWCgwXDTtBDRnawEU9XxLHUdfjHNPAwRT2-ec7kn2mzO4D2x3hZPqJsEH2zlHPKoW6-PfXo_6Wh65gnwZjowpS7vZconh5BpX31D4WmiP6hTwc27keS_MBI6ZVlVIk-pZhgytq3GRTbdcNLwqtfOfCiNGoqElIbSLlyvnb7FfnNtjWub3eyY9lCdgmLDqVh-POBbDVEZMz7WrD77WrOSvXXkfsC-t1Q"
cookies = parse_cookies(cookie_string)

# JSON-RPC payload
payload = json.dumps([
    {
        "method": "getUserSuppliers",
        "params": {},
        "id": "json-rpc_7",
        "jsonrpc": "2.0"
    }
])

# Отправка запроса
response = requests.post(url, headers=headers, cookies=cookies, data=payload)

# Обработка ответа
if response.status_code == 200:
    try:
        raw = response.json()

        for item in raw:
            suppliers_block = item.get("result", {}).get("suppliers", [])
            for supplier in suppliers_block:
                name = supplier.get("name")
                supplier_id = supplier.get("id")
                if name and supplier_id:
                    print(f"{name} — {supplier_id}")
        print(raw)
    except Exception as e:
        print("❌ Ошибка при обработке JSON:", e)
        print("📦 Raw response:", response.text)
else:
    print("❌ Ошибка запроса:", response.status_code)
    print("📦 Ответ сервера:", response.text)
