import requests

def parse_cookies(cookie_str):
    cookies = {}
    for item in cookie_str.split(";"):
        if "=" in item:
            key, value = item.strip().split("=", 1)
            cookies[key] = value
    return cookies

# ВСТАВЬ СЮДА СТРОКУ COOKIE
cookie_string = """
external-locale=ru;_wbauid=9833399961741863152;wbx-validation-key=4cbab275-ad85-4e21-9de2-2a87339969f9;current_feature_version=71FBB324-852E-422A-8F55-35BA4C629C18;landing_version_ru=EFD8FA05-7358-4E4C-9DE8-5608214FE1E4;locale=ru;WBTokenV3=eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE3NDE4NjMzNTAsInZlcnNpb24iOjIsInVzZXIiOiIxMzIyNjQzNDkiLCJzaGFyZF9rZXkiOiIyMSIsImNsaWVudF9pZCI6InNlbGxlci1wb3J0YWwiLCJzZXNzaW9uX2lkIjoiYTEyODdhMmEwZjMwNDFkZmI2YzgzYjM1Yjg0YjYyMmMiLCJ1c2VyX3JlZ2lzdHJhdGlvbl9kdCI6MTY5OTU1NDc0MywidmFsaWRhdGlvbl9rZXkiOiIzNzk4ZmRkMGZiNTc3NjYxMzBhN2JhNzM4MGE3YzhmZTc4MTc1Zjc3OWVjMTAwN2M0ZDM3NjA5YjVjMzNlMTc3In0.WngkegFvjFcUixzgFIThIl6ihU8cENVmajs3BMOcaGIxyNXTvxL2K-E4jrBd-dNO0L4v3AgrbA3yB3Dvy79Yz9RXvikOd4jikPqCbQpY-As61JqEM8XB9PWtmc_RLiPR3GZiTrmdAJ8GN6pvH8gxt1zeY7I2ckqoGfyBkVfKBVRjcMZyoCnneG1RH4J2ph5ApYiN0WjEeBF3O7UB7-AfnVyP1TKVfRvZbACeYpmXhnqCWQYa2WWsQtRvgGoGKmvGWgvdm921__9_L8g2Lz7YMQsUbGHx87Q0cJVl4lfO_V3RlvrKRGtb6vXJdARWsSx43jPZRDuAtpPW8ygO4Qyihw;x-supplier-id=451b6285-cd7c-4975-98e7-c382bc3d2fb5;x-supplier-id-external=451b6285-cd7c-4975-98e7-c382bc3d2fb5
""".strip()

# ВСТАВЬ СЮДА АКТУАЛЬНЫЙ authorizev3 токен
WBTokenV3 = "qwerty"


# Парсим куки
cookies = parse_cookies(cookie_string)

# URL для обновления токена
url = "https://seller.wildberries.ru/upgrade-cookie-authv3"

# Заголовки
headers = {
    "accept": "*/*",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "ru,en-US;q=0.9,en;q=0.8",
    "authorizev3": WBTokenV3,
    "cache-control": "no-cache",
    "content-type": "application/json",
    "origin": "https://seller.wildberries.ru",
    "pragma": "no-cache",
    "referer": "https://seller.wildberries.ru/",
    "sec-ch-ua": '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    "content-length": "0"
}

# Отправляем POST-запрос
response = requests.post(url, headers=headers, cookies=cookies)

# Обрабатываем ответ
print("Status Code:", response.status_code)

# Проверяем, пришел ли новый токен
if "set-cookie" in response.headers:
    set_cookie = response.headers["set-cookie"]
    if "WBTokenV3=" in set_cookie:
        new_token = set_cookie.split("WBTokenV3=")[1].split(";")[0]
        print("\n🔄 Новый WBTokenV3:")
        print(new_token)
    else:
        print("⚠️ Токен WBTokenV3 не найден в заголовке Set-Cookie.")
else:
    print("⚠️ Заголовок Set-Cookie отсутствует.")
