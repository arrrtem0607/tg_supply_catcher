import requests
import json

# URL запроса
url = "https://seller.wildberries.ru/ns/suppliers/suppliers-portal-core/suppliers"

# Авторизационный токен (замени на актуальный)
WBTokenV3 = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE3NDMwNzQ5NDQsInZlcnNpb24iOjIsInVzZXIiOiI1NTgzODg4MSIsInNoYXJkX2tleSI6IjE2IiwiY2xpZW50X2lkIjoic2VsbGVyLXBvcnRhbCIsInNlc3Npb25faWQiOiI0YWE3M2IyNDYyMTM0ZTNiYmZmOTRhMTQzZTE0M2M1YSIsInVzZXJfcmVnaXN0cmF0aW9uX2R0IjoxNjc0MDUwMDg0LCJ2YWxpZGF0aW9uX2tleSI6IjExY2ZmMWQ0ZmQzNWNjMmNkMjFmNDhjMTNhMjQwMGM5MmJiMzU3NmU4MzU5NjNjM2ZlNGVjMzdhNjYzYmUyMzQifQ.DO2AasLeRCrN24WtO0y6DBbX_9nmNCVeWjrBR9X_ho00bxgRrVVZUSEtJOyDDqCvpbjjn-KwtD_RDnfbwKZBV12QwkR6XRDW8iESDqiM9amlyE9gdv_a7wZrCBe2z-51PjzrQAPfKlosbPbAtTyUeC3P1CQ_LwBFv7v1YP1-USgSf5FrgANTWDqwh40huuPE36pw5dsYprrscuKk2_PKzqPZ8LFrPwwJEpKFmYqh3656RUqkQJwCtTx0vq-7KysFKwzzaodwEBCD3GWKnkvkDv5X-4uJwiKQD92mcKblcMLfARMRgN0EvpCz1GnueGADatm2VBWsZL-OhEz1pEx9uQ"

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
cookie_string = "cfidsw-wb=1FpTGYZIVMzHvFiww5fb3skTZScc5BkGgBFt5/6fnZyCvSXqj8mGZAkUlJK0gJ+2FnNddunxEoNhhNrpquEzl7SUX2LRpiENAEgOIWiXTlzCm5JCxL3Y/VOQraMmWEGk0QNMeBw7XPeYE+wSVM/qfhQHk5IGabyR18w/Jk6g;external-locale=ru;x-nextjs-country=ru;__zzatw-wb=MDA0dC0cTHtmcDhhDHEWTT17CT4VHThHKHIzd2UuQG0gZ09hIDVRP0FaW1Q4NmdBEXUmCQg3LGBwVxlRExpceEdXeiwcGH1xJ1d/DFxBQmllbQwtUlFRS19/Dg4/aU5ZQ11wS3E6EmBWGB5CWgtMeFtLKRZHGzJhXkZpdRVUCj9fPUUmdVw+ZSVjeWImdBEJCFkiRHxrVAwIEl5uRF9vG3siXyoIJGM1Xz9EaVhTMCpYQXt1J3Z+KmUzPGwgZk1fI0tVTnopGw1pN2wXPHVlLwkxLGJ5MVIvE0tsP0caRFpbQDsyVghDQE1HFF9BWncyUlFRS2EQR0lrZU5TQixmG3EVTQgNND1aciIPWzklWAgSPwsmIBR+cSlTDwtcPkVvbxt/Nl0cOWMRCxl+OmNdRkc3FSR7dSYKCTU3YnAvTCB7SykWRxsyYV5GaXUVUDw8ZD12KnMmcR4iGURdIEdWSglaIUR0KCkMD0EYcnVudjJwVxlRDxZhDhYYRRcje0I3Yhk4QhgvPV8/YngiD2lIYCJKW1N9LRkSeWslS3FPLH12X30beylOIA0lVBMhP05yylYdGg==;_wbauid=710225201732259636;wbx-validation-key=d4ee9997-0f43-45cc-a426-9669aec81c1a;__zzatw-wb=MDA0dC0cTHtmcDhhDHEWTT17CT4VHThHKHIzd2UuQG0gZ09hIDVRP0FaW1Q4NmdBEXUmCQg3LGBwVxlRExpceEdXeiwcGH1xJ1d/DFxBQmllbQwtUlFRS19/Dg4/aU5ZQ11wS3E6EmBWGB5CWgtMeFtLKRZHGzJhXkZpdRVUCj9fPUUmdVw+ZSVjeWImdBEJCFkiRHxrVAwIEl5uRF9vG3siXyoIJGM1Xz9EaVhTMCpYQXt1J3Z+KmUzPGwgZk1fI0tVTnopGw1pN2wXPHVlLwkxLGJ5MVIvE0tsP0caRFpbQDsyVghDQE1HFF9BWncyUlFRS2EQR0lrZU5TQixmG3EVTQgNND1aciIPWzklWAgSPwsmIBR+cSlTDwtcPkVvbxt/Nl0cOWMRCxl+OmNdRkc3FSR7dSYKCTU3YnAvTCB7SykWRxsyYV5GaXUVUDw8ZD12KnMmcR4iGURdIEdWSglaIUR0KCkMD0EYcnVudjJwVxlRDxZhDhYYRRcje0I3Yhk4QhgvPV8/YngiD2lIYCJKW1N9LRkSeWslS3FPLH12X30beylOIA0lVBMhP05yylYdGg==;_ym_d=1733928533;_ym_uid=1731447877677930150;cfidsw-wb=1FpTGYZIVMzHvFiww5fb3skTZScc5BkGgBFt5/6fnZyCvSXqj8mGZAkUlJK0gJ+2FnNddunxEoNhhNrpquEzl7SUX2LRpiENAEgOIWiXTlzCm5JCxL3Y/VOQraMmWEGk0QNMeBw7XPeYE+wSVM/qfhQHk5IGabyR18w/Jk6g;current_feature_version=E598F9C9-A7B9-478E-BBCD-A8B4DAD79DD9;landing_version_ru=EFD8FA05-7358-4E4C-9DE8-5608214FE1E4;locale=ru;WBTokenV3=eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE3NDMxNjAzNjQsInZlcnNpb24iOjIsInVzZXIiOiI1NTgzODg4MSIsInNoYXJkX2tleSI6IjE2IiwiY2xpZW50X2lkIjoic2VsbGVyLXBvcnRhbCIsInNlc3Npb25faWQiOiIzY2Y5N2EzYjcxYmM0ZGJhODQzMmRjYzc5YWQxODcwNyIsInVzZXJfcmVnaXN0cmF0aW9uX2R0IjoxNjc0MDUwMDg0LCJ2YWxpZGF0aW9uX2tleSI6IjExY2ZmMWQ0ZmQzNWNjMmNkMjFmNDhjMTNhMjQwMGM5MmJiMzU3NmU4MzU5NjNjM2ZlNGVjMzdhNjYzYmUyMzQifQ.IsZj5PAPL1egqc6uwM9A9iQAF6MgqIwXaYfCjNWaDQka1MHbaBVM2Wx8XrA1zdjCS-wmn1-Y6L-NroOdXjw2Nz5PPBRDs5wSFBgXXjhjGwclMM-eD7-aCuOnroi7XIAnP0zIo91hzb6QoGBu_bw5uXR1eOC0hHVPUtPeS2JeAl3-c-7HwCNcEMVhk3L-yag4fdVaI9g30oAHStxPAm_iaFusQVvCCMIn7o9crv0cORifPwWzyS4xFO0GzfU_ningP1LYNHmePr57YbAJjewZuNp0rDyz3iQ5N95_60UdW7vpVA1qdHSn8hrly7Chpe36n-P-s3TZF1JkRypDUWv5aw"
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
    except Exception as e:
        print("❌ Ошибка при обработке JSON:", e)
        print("📦 Raw response:", response.text)
else:
    print("❌ Ошибка запроса:", response.status_code)
    print("📦 Ответ сервера:", response.text)
