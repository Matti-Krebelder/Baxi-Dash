import requests
from cryptography.fernet import Fernet
from reds_simple_logger import Logger

logger = Logger()

class Get_Data:
    def __init__(self, encryption_key, api_key):
        self.encryption_key:str = encryption_key
        self.api_key = api_key
        
    

    class Response:
        def __init__(self, data, key):
            fernet = Fernet(key)
            self.tocken = f"{fernet.decrypt(data['tocken']).decode()}"
            self.client_id = data["client_id"]
            self.client_secret = f"{fernet.decrypt(data['client_secret']).decode()}"
            self.redirect_uri = data["redirect_uri"]
            self.app_name = data["app_name"]
            self.app_id = data["app_id"]
            self.app_verified = data["app_verified"]
        

    def baxi_data_pull(self):
        try:
            headers = {
                'Authorization': f"{self.api_key}"
            }
            request = requests.get("https://baxi-backend.pyropixle.com/api/oauth/get/data/baxi", headers=headers)
            response = request.json()
            return self.Response(response, self.encryption_key)
        except Exception as e:
            logger.error("ERROR: " + str(e))
        
        
        