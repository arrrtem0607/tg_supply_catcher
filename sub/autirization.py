import requests
import subprocess
import json

def parse_cookies(cookie_str):
    cookies = {}
    for item in cookie_str.split(";"):
        if "=" in item:
            key, value = item.strip().split("=", 1)
            cookies[key] = value
    return cookies

class WildberriesAuth:
    @staticmethod
    def get_captcha_token():
        """Fetch and solve captcha, returning the token."""
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

    def __init__(self, phone_number: str, cookie_string: str):
        self.phone_number = phone_number
        self.sticker = None  # <=== добавляем!
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
        self.session.cookies.update(parse_cookies(cookie_string))

    def send_code(self):
        captcha_token = self.get_captcha_token()
        code_url = "https://seller-auth.wildberries.ru/auth/v2/code/wb-captcha"
        payload = {
            "phone_number": self.phone_number,
            "captcha_token": captcha_token
        }
        response = self.session.post(code_url, json=payload)
        print("🔐 Запрос кода:", response.status_code, response.text)

        if response.ok:
            data = response.json()
            self.sticker = data.get("payload", {}).get("sticker")  # <=== сохраняем сюда
        return response.ok

    def authorize(self, code: str):
        auth_url = "https://seller-auth.wildberries.ru/auth/v2/auth"
        payload = {
            "sticker": self.sticker,
            "code": int(code)
        }
        response = self.session.post(auth_url, json=payload)
        print("✅ Авторизация:", response.status_code)
        print("Ответ:", response.json())
        print("Set-Cookie:", response.headers.get("set-cookie"))


if __name__ == "__main__":
    cookie_string = """cfidsw-wb=1FpTGYZIVMzHvFiww5fb3skTZScc5BkGgBFt5/6fnZyCvSXqj8mGZAkUlJK0gJ+2FnNddunxEoNhhNrpquEzl7SUX2LRpiENAEgOIWiXTlzCm5JCxL3Y/VOQraMmWEGk0QNMeBw7XPeYE+wSVM/qfhQHk5IGabyR18w/Jk6g;external-locale=ru;x-nextjs-country=ru;__zzatw-wb=MDA0dC0cTHtmcDhhDHEWTT17CT4VHThHKHIzd2UuQG0gZ09hIDVRP0FaW1Q4NmdBEXUmCQg3LGBwVxlRExpceEdXeiwcGH1xJ1d/DFxBQmllbQwtUlFRS19/Dg4/aU5ZQ11wS3E6EmBWGB5CWgtMeFtLKRZHGzJhXkZpdRVUCj9fPUUmdVw+ZSVjeWImdBEJCFkiRHxrVAwIEl5uRF9vG3siXyoIJGM1Xz9EaVhTMCpYQXt1J3Z+KmUzPGwgZk1fI0tVTnopGw1pN2wXPHVlLwkxLGJ5MVIvE0tsP0caRFpbQDsyVghDQE1HFF9BWncyUlFRS2EQR0lrZU5TQixmG3EVTQgNND1aciIPWzklWAgSPwsmIBR+cSlTDwtcPkVvbxt/Nl0cOWMRCxl+OmNdRkc3FSR7dSYKCTU3YnAvTCB7SykWRxsyYV5GaXUVUDw8ZD12KnMmcR4iGURdIEdWSglaIUR0KCkMD0EYcnVudjJwVxlRDxZhDhYYRRcje0I3Yhk4QhgvPV8/YngiD2lIYCJKW1N9LRkSeWslS3FPLH12X30beylOIA0lVBMhP05yylYdGg==;_wbauid=710225201732259636;wbx-validation-key=d4ee9997-0f43-45cc-a426-9669aec81c1a;__zzatw-wb=MDA0dC0cTHtmcDhhDHEWTT17CT4VHThHKHIzd2UuQG0gZ09hIDVRP0FaW1Q4NmdBEXUmCQg3LGBwVxlRExpceEdXeiwcGH1xJ1d/DFxBQmllbQwtUlFRS19/Dg4/aU5ZQ11wS3E6EmBWGB5CWgtMeFtLKRZHGzJhXkZpdRVUCj9fPUUmdVw+ZSVjeWImdBEJCFkiRHxrVAwIEl5uRF9vG3siXyoIJGM1Xz9EaVhTMCpYQXt1J3Z+KmUzPGwgZk1fI0tVTnopGw1pN2wXPHVlLwkxLGJ5MVIvE0tsP0caRFpbQDsyVghDQE1HFF9BWncyUlFRS2EQR0lrZU5TQixmG3EVTQgNND1aciIPWzklWAgSPwsmIBR+cSlTDwtcPkVvbxt/Nl0cOWMRCxl+OmNdRkc3FSR7dSYKCTU3YnAvTCB7SykWRxsyYV5GaXUVUDw8ZD12KnMmcR4iGURdIEdWSglaIUR0KCkMD0EYcnVudjJwVxlRDxZhDhYYRRcje0I3Yhk4QhgvPV8/YngiD2lIYCJKW1N9LRkSeWslS3FPLH12X30beylOIA0lVBMhP05yylYdGg==;_ym_d=1733928533;_ym_uid=1731447877677930150;cfidsw-wb=1FpTGYZIVMzHvFiww5fb3skTZScc5BkGgBFt5/6fnZyCvSXqj8mGZAkUlJK0gJ+2FnNddunxEoNhhNrpquEzl7SUX2LRpiENAEgOIWiXTlzCm5JCxL3Y/VOQraMmWEGk0QNMeBw7XPeYE+wSVM/qfhQHk5IGabyR18w/Jk6g;current_feature_version=3794F7FB-6F51-4046-A5E6-1676BB6FA0F6;landing_version_ru=EFD8FA05-7358-4E4C-9DE8-5608214FE1E4;locale=ru;WBTokenV3=eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE3NDMwNzQ5NDQsInZlcnNpb24iOjIsInVzZXIiOiI1NTgzODg4MSIsInNoYXJkX2tleSI6IjE2IiwiY2xpZW50X2lkIjoic2VsbGVyLXBvcnRhbCIsInNlc3Npb25faWQiOiI0YWE3M2IyNDYyMTM0ZTNiYmZmOTRhMTQzZTE0M2M1YSIsInVzZXJfcmVnaXN0cmF0aW9uX2R0IjoxNjc0MDUwMDg0LCJ2YWxpZGF0aW9uX2tleSI6IjExY2ZmMWQ0ZmQzNWNjMmNkMjFmNDhjMTNhMjQwMGM5MmJiMzU3NmU4MzU5NjNjM2ZlNGVjMzdhNjYzYmUyMzQifQ.DO2AasLeRCrN24WtO0y6DBbX_9nmNCVeWjrBR9X_ho00bxgRrVVZUSEtJOyDDqCvpbjjn-KwtD_RDnfbwKZBV12QwkR6XRDW8iESDqiM9amlyE9gdv_a7wZrCBe2z-51PjzrQAPfKlosbPbAtTyUeC3P1CQ_LwBFv7v1YP1-USgSf5FrgANTWDqwh40huuPE36pw5dsYprrscuKk2_PKzqPZ8LFrPwwJEpKFmYqh3656RUqkQJwCtTx0vq-7KysFKwzzaodwEBCD3GWKnkvkDv5X-4uJwiKQD92mcKblcMLfARMRgN0EvpCz1GnueGADatm2VBWsZL-OhEz1pEx9uQ;x-supplier-id=da665472-99a9-4df2-8a47-3965ef62a1a6;x-supplier-id-external=da665472-99a9-4df2-8a47-3965ef62a1a6"""  # Вставь свои куки
    phone = "79161823436"

    wb = WildberriesAuth(phone, cookie_string)
    if wb.send_code():
        sms_code = input("Введите код из SMS: ")
        wb.authorize(sms_code)
