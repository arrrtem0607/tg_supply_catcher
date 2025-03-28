import requests

url = "https://seller.wildberries.ru/ns/passport-portal/suppliers-portal-ru/validate"
WBTokenV3 = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE3NDMxNjAzNjQsInZlcnNpb24iOjIsInVzZXIiOiI1NTgzODg4MSIsInNoYXJkX2tleSI6IjE2IiwiY2xpZW50X2lkIjoic2VsbGVyLXBvcnRhbCIsInNlc3Npb25faWQiOiIzY2Y5N2EzYjcxYmM0ZGJhODQzMmRjYzc5YWQxODcwNyIsInVzZXJfcmVnaXN0cmF0aW9uX2R0IjoxNjc0MDUwMDg0LCJ2YWxpZGF0aW9uX2tleSI6IjExY2ZmMWQ0ZmQzNWNjMmNkMjFmNDhjMTNhMjQwMGM5MmJiMzU3NmU4MzU5NjNjM2ZlNGVjMzdhNjYzYmUyMzQifQ.IsZj5PAPL1egqc6uwM9A9iQAF6MgqIwXaYfCjNWaDQka1MHbaBVM2Wx8XrA1zdjCS-wmn1-Y6L-NroOdXjw2Nz5PPBRDs5wSFBgXXjhjGwclMM-eD7-aCuOnroi7XIAnP0zIo91hzb6QoGBu_bw5uXR1eOC0hHVPUtPeS2JeAl3-c-7HwCNcEMVhk3L-yag4fdVaI9g30oAHStxPAm_iaFusQVvCCMIn7o9crv0cORifPwWzyS4xFO0GzfU_ningP1LYNHmePr57YbAJjewZuNp0rDyz3iQ5N95_60UdW7vpVA1qdHSn8hrly7Chpe36n-P-s3TZF1JkRypDUWv5aw"

headers = {
    "accept": "*/*",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "ru,en-US;q=0.9,en;q=0.8",
    "authorizev3": WBTokenV3,  # Подставь актуальный токен
    "cache-control": "no-cache",
    "content-length": "0",
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
}

def parse_cookies(cookie_str):
    cookies = {}
    for item in cookie_str.split(";"):
        if "=" in item:
            key, value = item.strip().split("=", 1)
            cookies[key] = value
    return cookies

cookie_string = """
cfidsw-wb=1FpTGYZIVMzHvFiww5fb3skTZScc5BkGgBFt5/6fnZyCvSXqj8mGZAkUlJK0gJ+2FnNddunxEoNhhNrpquEzl7SUX2LRpiENAEgOIWiXTlzCm5JCxL3Y/VOQraMmWEGk0QNMeBw7XPeYE+wSVM/qfhQHk5IGabyR18w/Jk6g;external-locale=ru;__zzatw-wb=MDA0dC0cTHtmcDhhDHEWTT17CT4VHThHKHIzd2UuQG0gZ09hIDVRP0FaW1Q4NmdBEXUmCQg3LGBwVxlRExpceEdXeiwcGH1xJ1d/DFxBQmllbQwtUlFRS19/Dg4/aU5ZQ11wS3E6EmBWGB5CWgtMeFtLKRZHGzJhXkZpdRVUCj9fPUUmdVw+ZSVjeWImdBEJCFkiRHxrVAwIEl5uRF9vG3siXyoIJGM1Xz9EaVhTMCpYQXt1J3Z+KmUzPGwgZk1fI0tVTnopGw1pN2wXPHVlLwkxLGJ5MVIvE0tsP0caRFpbQDsyVghDQE1HFF9BWncyUlFRS2EQR0lrZU5TQixmG3EVTQgNND1aciIPWzklWAgSPwsmIBR+cSlTDwtcPkVvbxt/Nl0cOWMRCxl+OmNdRkc3FSR7dSYKCTU3YnAvTCB7SykWRxsyYV5GaXUVUDw8ZD12KnMmcR4iGURdIEdWSglaIUR0KCkMD0EYcnVudjJwVxlRDxZhDhYYRRcje0I3Yhk4QhgvPV8/YngiD2lIYCJKW1N9LRkSeWslS3FPLH12X30beylOIA0lVBMhP05yylYdGg==;_wbauid=710225201732259636;wbx-validation-key=d4ee9997-0f43-45cc-a426-9669aec81c1a;__zzatw-wb=MDA0dC0cTHtmcDhhDHEWTT17CT4VHThHKHIzd2UuQG0gZ09hIDVRP0FaW1Q4NmdBEXUmCQg3LGBwVxlRExpceEdXeiwcGH1xJ1d/DFxBQmllbQwtUlFRS19/Dg4/aU5ZQ11wS3E6EmBWGB5CWgtMeFtLKRZHGzJhXkZpdRVUCj9fPUUmdVw+ZSVjeWImdBEJCFkiRHxrVAwIEl5uRF9vG3siXyoIJGM1Xz9EaVhTMCpYQXt1J3Z+KmUzPGwgZk1fI0tVTnopGw1pN2wXPHVlLwkxLGJ5MVIvE0tsP0caRFpbQDsyVghDQE1HFF9BWncyUlFRS2EQR0lrZU5TQixmG3EVTQgNND1aciIPWzklWAgSPwsmIBR+cSlTDwtcPkVvbxt/Nl0cOWMRCxl+OmNdRkc3FSR7dSYKCTU3YnAvTCB7SykWRxsyYV5GaXUVUDw8ZD12KnMmcR4iGURdIEdWSglaIUR0KCkMD0EYcnVudjJwVxlRDxZhDhYYRRcje0I3Yhk4QhgvPV8/YngiD2lIYCJKW1N9LRkSeWslS3FPLH12X30beylOIA0lVBMhP05yylYdGg==;_ym_d=1733928533;_ym_uid=1731447877677930150;cfidsw-wb=1FpTGYZIVMzHvFiww5fb3skTZScc5BkGgBFt5/6fnZyCvSXqj8mGZAkUlJK0gJ+2FnNddunxEoNhhNrpquEzl7SUX2LRpiENAEgOIWiXTlzCm5JCxL3Y/VOQraMmWEGk0QNMeBw7XPeYE+wSVM/qfhQHk5IGabyR18w/Jk6g;current_feature_version=3794F7FB-6F51-4046-A5E6-1676BB6FA0F6;locale=ru;WBTokenV3=eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE3NDE4NjI2OTIsInZlcnNpb24iOjIsInVzZXIiOiI1NTgzODg4MSIsInNoYXJkX2tleSI6IjE2IiwiY2xpZW50X2lkIjoic2VsbGVyLXBvcnRhbCIsInNlc3Npb25faWQiOiIzMTY5YWMzMjczNzY0ZTZjYWM4N2NiM2M2YmMyYTFjYyIsInVzZXJfcmVnaXN0cmF0aW9uX2R0IjoxNjc0MDUwMDg0LCJ2YWxpZGF0aW9uX2tleSI6IjExY2ZmMWQ0ZmQzNWNjMmNkMjFmNDhjMTNhMjQwMGM5MmJiMzU3NmU4MzU5NjNjM2ZlNGVjMzdhNjYzYmUyMzQifQ.bXnQiRSOPHZfo3VGQ0OPqos3vPZIq5DpN4n9ZVvY84AL9OMJQWNLT3yqzYC742U7u-5jg3gA7wwlRBkkllMfolbWG1mkD6yUDY1MfaDenNihcfFVPmKennS1CKTFVWUtu6PN-13QVMdnCWYY5aRDPpAyl59i4F2lb1KcdQ9WUQaLl0YKB9wmhxorEPLPFftfpUDsKz1jKAHLbKf4snw0vcS2xTbtlpbrHTIaKBbWHtYIeF-_35iwik5R7cEba-swiTTjHTTiMfD09ZNiD64611RTLC4IaIzCyTrCY9Yc3ih_N713Nm7s5wqLLl5FEFHGm9bH-EYMLJ8bUJfjxkSpdw;x-supplier-id=1ea90ee0-fa5b-4141-8e8c-e6e8feed139e;x-supplier-id-external=1ea90ee0-fa5b-4141-8e8c-e6e8feed139e
""".strip()

cookies = parse_cookies(cookie_string)

# Пустой payload
response = requests.post(url, headers=headers, cookies=cookies)

print(response.cookies)
print("Status Code:", response.status_code)
print("Response Text:", response.text)
