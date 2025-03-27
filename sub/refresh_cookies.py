import requests
import time

# === НАСТРОЙКИ ===
validate_url = "https://seller.wildberries.ru/ns/passport-portal/suppliers-portal-ru/validate"
refresh_url = "https://seller.wildberries.ru/upgrade-cookie-authv3"

# Подставь актуальные токен и куки
WBTokenV3 = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE3NDMwNzQ5NDQsInZlcnNpb24iOjIsInVzZXIiOiI1NTgzODg4MSIsInNoYXJkX2tleSI6IjE2IiwiY2xpZW50X2lkIjoic2VsbGVyLXBvcnRhbCIsInNlc3Npb25faWQiOiI0YWE3M2IyNDYyMTM0ZTNiYmZmOTRhMTQzZTE0M2M1YSIsInVzZXJfcmVnaXN0cmF0aW9uX2R0IjoxNjc0MDUwMDg0LCJ2YWxpZGF0aW9uX2tleSI6IjExY2ZmMWQ0ZmQzNWNjMmNkMjFmNDhjMTNhMjQwMGM5MmJiMzU3NmU4MzU5NjNjM2ZlNGVjMzdhNjYzYmUyMzQifQ.DO2AasLeRCrN24WtO0y6DBbX_9nmNCVeWjrBR9X_ho00bxgRrVVZUSEtJOyDDqCvpbjjn-KwtD_RDnfbwKZBV12QwkR6XRDW8iESDqiM9amlyE9gdv_a7wZrCBe2z-51PjzrQAPfKlosbPbAtTyUeC3P1CQ_LwBFv7v1YP1-USgSf5FrgANTWDqwh40huuPE36pw5dsYprrscuKk2_PKzqPZ8LFrPwwJEpKFmYqh3656RUqkQJwCtTx0vq-7KysFKwzzaodwEBCD3GWKnkvkDv5X-4uJwiKQD92mcKblcMLfARMRgN0EvpCz1GnueGADatm2VBWsZL-OhEz1pEx9uQ"
cookie_string = "cfidsw-wb=1FpTGYZIVMzHvFiww5fb3skTZScc5BkGgBFt5/6fnZyCvSXqj8mGZAkUlJK0gJ+2FnNddunxEoNhhNrpquEzl7SUX2LRpiENAEgOIWiXTlzCm5JCxL3Y/VOQraMmWEGk0QNMeBw7XPeYE+wSVM/qfhQHk5IGabyR18w/Jk6g;external-locale=ru;x-nextjs-country=ru;__zzatw-wb=MDA0dC0cTHtmcDhhDHEWTT17CT4VHThHKHIzd2UuQG0gZ09hIDVRP0FaW1Q4NmdBEXUmCQg3LGBwVxlRExpceEdXeiwcGH1xJ1d/DFxBQmllbQwtUlFRS19/Dg4/aU5ZQ11wS3E6EmBWGB5CWgtMeFtLKRZHGzJhXkZpdRVUCj9fPUUmdVw+ZSVjeWImdBEJCFkiRHxrVAwIEl5uRF9vG3siXyoIJGM1Xz9EaVhTMCpYQXt1J3Z+KmUzPGwgZk1fI0tVTnopGw1pN2wXPHVlLwkxLGJ5MVIvE0tsP0caRFpbQDsyVghDQE1HFF9BWncyUlFRS2EQR0lrZU5TQixmG3EVTQgNND1aciIPWzklWAgSPwsmIBR+cSlTDwtcPkVvbxt/Nl0cOWMRCxl+OmNdRkc3FSR7dSYKCTU3YnAvTCB7SykWRxsyYV5GaXUVUDw8ZD12KnMmcR4iGURdIEdWSglaIUR0KCkMD0EYcnVudjJwVxlRDxZhDhYYRRcje0I3Yhk4QhgvPV8/YngiD2lIYCJKW1N9LRkSeWslS3FPLH12X30beylOIA0lVBMhP05yylYdGg==;_wbauid=710225201732259636;wbx-validation-key=d4ee9997-0f43-45cc-a426-9669aec81c1a;__zzatw-wb=MDA0dC0cTHtmcDhhDHEWTT17CT4VHThHKHIzd2UuQG0gZ09hIDVRP0FaW1Q4NmdBEXUmCQg3LGBwVxlRExpceEdXeiwcGH1xJ1d/DFxBQmllbQwtUlFRS19/Dg4/aU5ZQ11wS3E6EmBWGB5CWgtMeFtLKRZHGzJhXkZpdRVUCj9fPUUmdVw+ZSVjeWImdBEJCFkiRHxrVAwIEl5uRF9vG3siXyoIJGM1Xz9EaVhTMCpYQXt1J3Z+KmUzPGwgZk1fI0tVTnopGw1pN2wXPHVlLwkxLGJ5MVIvE0tsP0caRFpbQDsyVghDQE1HFF9BWncyUlFRS2EQR0lrZU5TQixmG3EVTQgNND1aciIPWzklWAgSPwsmIBR+cSlTDwtcPkVvbxt/Nl0cOWMRCxl+OmNdRkc3FSR7dSYKCTU3YnAvTCB7SykWRxsyYV5GaXUVUDw8ZD12KnMmcR4iGURdIEdWSglaIUR0KCkMD0EYcnVudjJwVxlRDxZhDhYYRRcje0I3Yhk4QhgvPV8/YngiD2lIYCJKW1N9LRkSeWslS3FPLH12X30beylOIA0lVBMhP05yylYdGg==;_ym_d=1733928533;_ym_uid=1731447877677930150;cfidsw-wb=1FpTGYZIVMzHvFiww5fb3skTZScc5BkGgBFt5/6fnZyCvSXqj8mGZAkUlJK0gJ+2FnNddunxEoNhhNrpquEzl7SUX2LRpiENAEgOIWiXTlzCm5JCxL3Y/VOQraMmWEGk0QNMeBw7XPeYE+wSVM/qfhQHk5IGabyR18w/Jk6g;current_feature_version=3794F7FB-6F51-4046-A5E6-1676BB6FA0F6;landing_version_ru=EFD8FA05-7358-4E4C-9DE8-5608214FE1E4;locale=ru;WBTokenV3=eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE3NDMwNzQ5NDQsInZlcnNpb24iOjIsInVzZXIiOiI1NTgzODg4MSIsInNoYXJkX2tleSI6IjE2IiwiY2xpZW50X2lkIjoic2VsbGVyLXBvcnRhbCIsInNlc3Npb25faWQiOiI0YWE3M2IyNDYyMTM0ZTNiYmZmOTRhMTQzZTE0M2M1YSIsInVzZXJfcmVnaXN0cmF0aW9uX2R0IjoxNjc0MDUwMDg0LCJ2YWxpZGF0aW9uX2tleSI6IjExY2ZmMWQ0ZmQzNWNjMmNkMjFmNDhjMTNhMjQwMGM5MmJiMzU3NmU4MzU5NjNjM2ZlNGVjMzdhNjYzYmUyMzQifQ.DO2AasLeRCrN24WtO0y6DBbX_9nmNCVeWjrBR9X_ho00bxgRrVVZUSEtJOyDDqCvpbjjn-KwtD_RDnfbwKZBV12QwkR6XRDW8iESDqiM9amlyE9gdv_a7wZrCBe2z-51PjzrQAPfKlosbPbAtTyUeC3P1CQ_LwBFv7v1YP1-USgSf5FrgANTWDqwh40huuPE36pw5dsYprrscuKk2_PKzqPZ8LFrPwwJEpKFmYqh3656RUqkQJwCtTx0vq-7KysFKwzzaodwEBCD3GWKnkvkDv5X-4uJwiKQD92mcKblcMLfARMRgN0EvpCz1GnueGADatm2VBWsZL-OhEz1pEx9uQ;x-supplier-id=da665472-99a9-4df2-8a47-3965ef62a1a6;x-supplier-id-external=da665472-99a9-4df2-8a47-3965ef62a1a6"

# Функция для парсинга строки куки
def parse_cookies(cookie_str):
    cookies = {}
    for item in cookie_str.split(";"):
        if "=" in item:
            key, value = item.strip().split("=", 1)
            cookies[key] = value
    return cookies

# Заголовки для запросов
def make_headers(token):
    return {
        "accept": "*/*",
        "authorizev3": token,
        "origin": "https://seller.wildberries.ru",
        "referer": "https://seller.wildberries.ru/",
        "user-agent": "Mozilla/5.0",
        "content-type": "application/json"
    }

# Инициализация
cookies = parse_cookies(cookie_string)
previous_token = WBTokenV3

print("🔁 Запуск проверки валидности и обновления токена каждую минуту...")

while True:
    # === Шаг 1: Проверка валидности текущего токена ===
    validate_resp = requests.post(validate_url, headers=make_headers(previous_token), cookies=cookies)
    print(f"[{time.strftime('%H:%M:%S')}] Validate status: {validate_resp.status_code}")

    # === Шаг 2: Обновление токена ===
    refresh_resp = requests.post(refresh_url, headers=make_headers(previous_token), cookies=cookies)

    # === Шаг 3: Извлечение нового токена из cookies ===
    new_token = refresh_resp.cookies.get("WBTokenV3")

    if not new_token:
        print("⚠️ Новый токен не получен. Ждём следующую минуту...")
    else:
        if new_token != previous_token:
            print("✅ Новый токен получен и отличается от предыдущего!")
            print("Новый WBTokenV3:", new_token)
            break
        else:
            print("🔄 Токен остался прежним. Повторим через 60 секунд...")

    # Ждём минуту
    time.sleep(60)
