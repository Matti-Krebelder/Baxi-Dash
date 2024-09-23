from http.client import responses

import pyotp
import requests
from cryptography.fernet import Fernet
from quart import session
from reds_simple_logger import Logger

logger = Logger()


class Get_Data:
    def __init__(self, encryption_key, api_key):
        self.encryption_key: str = encryption_key
        self.api_key = api_key

    class Response:
        def __init__(self, data, key):
            fernet = Fernet(key)
            self.token = f"{fernet.decrypt(data['token']).decode()}"
            self.client_id = data["client_id"]
            self.client_secret = f"{fernet.decrypt(data['client_secret']).decode()}"
            self.redirect_uri = data["redirect_uri"]
            self.app_name = data["app_name"]
            self.app_id = data["app_id"]
            self.app_verified = data["app_verified"]
            self.secret = fernet.decrypt(data["secret"]).decode()

    def baxi_data_pull(self):
        try:
            headers = {"Authorization": f"{self.api_key}"}
            one_time_code = generate_one_time_code(baxi_data.secret)
            data = {"otc": one_time_code}
            request = requests.get(
                "https://baxi-backend.pyropixle.com/api/oauth/get/data/baxi",
                headers=headers,
                json=data
            )
            logger.debug.info(request.text)
            response = request.json()
            return self.Response(response, self.encryption_key)
        except Exception as e:
            logger.error("ERROR: " + str(e))


def get_active_systems(key: str, guild_id: int):
    headers = {"Authorization": f"{key}"}
    one_time_code = generate_one_time_code(baxi_data.secret)
    data = {"otc": one_time_code}

    request = requests.get(
        f"https://baxi-backend.pyropixle.com/api/dash/get/active_systems/{guild_id}",
        headers=headers,
        json=data
    )
    return request.json()


def generate_one_time_code(secret_key):
    totp = pyotp.TOTP(secret_key)
    return totp.now()
