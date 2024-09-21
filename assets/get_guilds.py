import requests
from reds_simple_logger import Logger

logger = Logger()


def get_user_guilds(token, api_endpoint):
    try:
        headers = {"Authorization": f"Bearer {token}"}
        user_guilds_response = requests.get(
            f"{api_endpoint}/users/@me/guilds", headers=headers
        )
        if user_guilds_response.status_code != 200:
            return {}, user_guilds_response.status_code
        user_guilds = user_guilds_response.json()
        return user_guilds
    except Exception as e:
        logger.error("Error in get_user_guilds: " + str(e))


def get_bot_guilds(token, api_endpoint):
    try:
        bot_headers = {"Authorization": f"Bot {str(token)}"}
        bot_guilds_response = requests.get(
            f"{api_endpoint}/users/@me/guilds", headers=bot_headers
        )
        if bot_guilds_response.status_code != 200:
            return {}, bot_guilds_response.status_code
        bot_guilds = bot_guilds_response.json()
        return bot_guilds
    except Exception as e:
        logger.error("Error in get_bot_guilds: " + str(e))
