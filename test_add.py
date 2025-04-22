import subprocess
import json
import requests
import pprint



pp = pprint.PrettyPrinter(indent=4, width=80, depth=None, compact=False)


def parse_cookies(cookies_str: str):
    cookies_dict = {}
    cookies = cookies_str.split(';')
    for cookie in cookies:
        key_value = cookie.strip().split('=', 1)
        if len(key_value) == 2:
            cookies_dict[key_value[0]] = key_value[1]
    return cookies_dict

def get_captcha_token():
    """Fetch and solve captcha, returning the token."""
    get_task_url = "https://pow.wb.ru/api/v1/short/get-task"
    verify_url = "https://pow.wb.ru/api/v1/short/verify-answer"
    response = requests.get(url=get_task_url)
    print(response.status_code)
    print(response.text)
    command = ['node', './wasm_exec.js', './solve.wasm', response.text]
    result = subprocess.run(command, capture_output=True, text=True)
    print(result.stdout)
    task_answer = json.loads(json.loads(result.stdout))
    print(task_answer)
    verify = requests.post(verify_url, json=task_answer)
    ret = json.loads(verify.text)['wb-captcha-short-token']
    print(ret)
    return ret

def _initialize_headers():
    headers = {
        "Accept": "*/*",
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep - alive',
        'Strict - Transport - Security': 'max - age = 31536000; preload;',
        'X - Content - Type - Options': 'nosniff',
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 YaBrowser/24.10.0.0 Safari/537.36"
    }
    return headers
headers = _initialize_headers()
cookies = "_wbauid=1124752961720057802; ___wbu=597759e4-9226-45c7-b103-c4f32dd03f19.1720057802; external-locale=ru; wb-pid=gYG1gkI1doRP_ZoaEQtZB59RAAABkQ-NJsWCwJplASsclp8De1iJ5hcxHIFoMoRQWoOgj3J_OC9MbQ; wb-id=gYEn47foTKtLRJ7pFwtA9qYvAAABkSSLLoBpWQrQs5lW4hL3c_w1lMx8yShda0CQrSmpLPYiPonzBWM0YjQ4NjMzLTBkMDItNDE3MS04MWFmLWNkMjVjZjUyNThjZA; wbx-validation-key=1a6d984d-07ed-4186-9ab1-557dd4cacc65; cfidsw-wb=eZ0zYP7Y0scz5EahmVMpS5ZPIZaSO1SSpBU07X68aMOrazHmXab3ZTc0u+jLXxXwEbuDmuxApEm1ast5L7vdB/AGPrXpEOTWzQXwi+P/ikyF0NLcFS1Puaz8BXWeuORAkZnyDXcmEFEpGb+AVYec6yOsevIaVvYmECDLpGmH; __zzatw-wb=MDA0dC0cTHtmcDhhDHEWTT17CT4VHThHKHIzd2UuQG0gZ09hIDVRP0FaW1Q4NmdBEXUmCQg3LGBwVxlRExpceEdXeiwcGH1vKVAOE2M+Q2llbQwtUlFRS19/Dg4/aU5ZQ11wS3E6EmBWGB5CWgtMeFtLKRZHGzJhXkZpdRVSDj9kQkFxeSlBZiVjTBckdFsIfCkbGn8mK1I8EWJxQl9vG3siXyoIJGM1Xz9EaVhTMCpYQXt1J3Z+KmUzPGwgZk1dJURcVQkmHA1pN2wXPHVlLwkxLGJ5MVIvE0tsP0caRFpbQDsyVghDQE1HFF9BWncyUlFRS2EQR0lrZU5TQixmG3EVTQgNND1aciIPWzklWAgSPwsmIBR+cSdVCBJjRUJwbxt/Nl0cOWMRCxl+OmNdRkc3FSR7dSYKCTU3YnAvTCB7SykWRxsyYV5GaXUVUDw8ZD12KnMmcR4iGURdIEdWSglaIUR0KCkMD0EYcnVudjJwVxlRDxZhDhYYRRcje0I3Yhk4QhgvPV8/YngiD2lIYCJKW1F/JiAZf3QrS3FPLH12X30beylOIA0lVBMhP05yniYO+Q==; x-supplier-id-external=1ea90ee0-fa5b-4141-8e8c-e6e8feed139e; WBTokenV3=eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE3NDMwNzY3MzksInZlcnNpb24iOjIsInVzZXIiOiI1NTgzODg4MSIsInNoYXJkX2tleSI6IjE2IiwiY2xpZW50X2lkIjoic2VsbGVyLXBvcnRhbCIsInNlc3Npb25faWQiOiIzN2Q5NTA0NjA2MTg0NWY1YTZjMzQyOThjODNlNjdkMSIsInVzZXJfcmVnaXN0cmF0aW9uX2R0IjoxNjc0MDUwMDg0LCJ2YWxpZGF0aW9uX2tleSI6ImU0YTIzYzRkYmMwZjNlMjQ4Mzc4MWU1M2E5NTI0Yzk2YTg4MWE1OGQxZjExZDUzYjIyZDcxOWQ2Y2JlNGMxMDEifQ.dGIfsta4DNV1kOa3PWx8Z8PAA3fiAChRny2bIVo_PVRZEWAUMcLKH_kmOAsw6w_JjTqlfBwvoKARzbZwaABXJdcXsa_I7ex5QpffviPVvFTRhZeqq6p075uNTnlPIxjvrwhULlGMFKptnVelbkcuLgu3Xn5yOgSIynYtcIYUpkDOhFJ-NOwgN4raE7psrqGK--8x7EZRZr2X5P7383P_h50FXqZwc49-DBYRURrPUJ2IwfDOcVpaJPqg4k_EGiWP2TLafqTy6-xa544rQ4f5jiUsJ7lkX0DpsdCZr3KeZOkR70uIrF4Df-_MlrAkkVdFpCxzd75UY2V4AjvlscTgIQ"
cookies = parse_cookies(cookies)
pp.pprint(cookies)
url = "https://seller-supply.wildberries.ru/ns/sm/supply-manager/api/v1/plan/add"
payload = {
    "params": {
        "preOrderId": 28276869,
        "deliveryDate": f"2025-04-26T00:00:00Z"
    },
    "jsonrpc": "2.0",
    "id": "json-rpc_54"
}
get_task_url = "https://pow.wb.ru/api/v1/short/get-task"
response = requests.get(url=get_task_url)
print(response.status_code)
print(repr(response.text))
response = response.text

command = ['node', './wasm_exec.js', './solve.wasm', response]
result = subprocess.run(command, capture_output=True, text=True)

task_answer = json.loads(json.loads(result.stdout))
print(repr(json.dumps(task_answer)))

verify_url = "https://pow.wb.ru/api/v1/short/verify-answer"
print(type(task_answer), task_answer)
verify = requests.post(verify_url, json=task_answer)
print(verify.status_code)
print(verify.text)
ret = json.loads(verify.text)['wb-captcha-short-token']

print(ret)

print(ret)
headers['x-wb-captcha-token'] = ret

response = requests.post(url, json=payload, cookies=cookies, headers=headers)
print(response.status_code)
print(response.headers)
print(response.text)

