import datetime
import os
import json
import threading
import time
import requests


class KeyValidator:
    def __init__(self):
        self.key_file = 'key.txt'
        self.api_url = 'https://service-9slkctpg-1258523888.gz.apigw.tencentcs.com/release/activate_key'

    def check_key_file(self):
        if not os.path.exists(self.key_file):
            self.create_key_file()
        else:
            self.process_key()

    def create_key_file(self):
        key = input("请输入卡号: ")
        with open(self.key_file, 'w') as f:
            f.write(key)
        self.validate_key(key)

    def process_key(self):
        with open(self.key_file, 'r') as f:
            key = f.read().strip()
        self.validate_key(key)

    def validate_key(self, key):
        data = {'key': key}
        response = requests.post(self.api_url, json=data)
        json_data = response.json()
        res_code = response.status_code

        if res_code == 200:
            status_code = json_data['status_code']
            message = json_data['message']
            if status_code == 200:
                expiration = datetime.datetime.strptime(
                    json_data['expiration'], "%a, %d %b %Y %H:%M:%S %Z")
                print(f"验证成功！消息: {message}，到期时间：{expiration}")
                self.save_key(key)
                self.start_expiration_thread(expiration)
            else:
                print(f"验证失败！消息: {message}")
                self.create_key_file()

        elif res_code == 400:
            print(f"验证失败！消息: 请求错误")
            self.create_key_file()

    def save_key(self, key):
        with open(self.key_file, 'w') as f:
            f.write(key)

    def check_expiration(self, expiration):
        current_time = datetime.datetime.now()
        while True:
            if expiration <= current_time:
                print("密钥已过期！")
                os._exit(1)
            time.sleep(60)

    def start_expiration_thread(self, expiration):
        expiration_thread = threading.Thread(
            target=self.check_expiration, args=(expiration,))
        expiration_thread.daemon = True
        expiration_thread.start()


# # 使用示例
# validator = KeyValidator()
# validator.check_key_file()

# # 主线程继续执行其他任务
# # ...
