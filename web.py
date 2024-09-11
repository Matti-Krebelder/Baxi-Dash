import json
import requests
import os
from quart import Quart, render_template, request, send_from_directory, jsonify, redirect, session
from quart_cors import cors
import configparser
from cryptography.fernet import Fernet

config = configparser.ConfigParser()
config.read("config/runtime.conf")

app = Quart(__name__, template_folder="Templates")
app = cors(app)
app.secret_key = os.urandom(24)
fernet = Fernet(config["BAXI"]["encryption_key"])

API_ENDPOINT = 'https://discord.com/api/v10'
AUTH_URL = 'https://discord.com/api/oauth2/authorize'
TOKEN_URL = 'https://discord.com/api/oauth2/token'
PERMS_API = 'https://baxi-backend.pyropixle.com/api/dash/check/staff/user/perms/'
LOG_FILE = 'denied_access.json'

headers = {
    'Authorization': f"{config['BAXI']['baxi_info_key']}"
}
baxi_data_request = requests.get("https://baxi-backend.pyropixle.com/api/oauth/get/data/baxi", headers=headers)
print(baxi_data_request.text)
baxi_data = baxi_data_request.json()

baxi_client_secret = f"{fernet.decrypt(baxi_data['client_secret']).decode()}"
baxi_tocken = f"{fernet.decrypt(baxi_data['tocken']).decode()}"

# Define the maintenance variable
maintenance = config.getboolean("DASH", "maintenance")

@app.route("/")
async def home():
    return redirect("https://baxi.pyropixle.com/dashboard")

@app.route("/login")
async def login():
    return redirect(f'{AUTH_URL}?client_id={int(baxi_data["client_id"])}&redirect_uri={baxi_data["redirect_uri"]}&response_type=code&scope=identify%20guilds')

@app.route("/callback")
async def callback():
    code = request.args.get('code')
    data = {
        'client_id': int(baxi_data["client_id"]),
        'client_secret': str(baxi_client_secret),
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': str(baxi_data["redirect_uri"])
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    r = requests.post(TOKEN_URL, data=data, headers=headers)
    r.raise_for_status()
    session['token'] = r.json()['access_token']
    return redirect('/dashboard')

DEFAULT_ICON = 'https://cdn.discordapp.com/embed/avatars/0.png' 


def log_denied_access(ip_address, user_id):
    """Append the IP address and user ID to the JSON log file."""
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'r') as file:
            denied_access = json.load(file)
    else:
        denied_access = []

    denied_access.append({
        'ip_address': ip_address,
        'user_id': user_id
    })

    with open(LOG_FILE, 'w') as file:
        json.dump(denied_access, file, indent=4)

def log_error(message):
    """Append error messages to a log file."""
    with open('error_log.json', 'a') as file:
        json.dump({'error': message}, file)
        file.write('\n')

@app.route("/dashboard")
async def dashboard():
    if 'token' not in session:
        return redirect('/login')

    headers = {'Authorization': f'Bearer {session["token"]}'}

    try:
        # Fetch user guilds (servers)
        user_guilds_response = requests.get(f'{API_ENDPOINT}/users/@me/guilds', headers=headers)
        user_guilds_response.raise_for_status()
        user_guilds = user_guilds_response.json()

        # Fetch bot guilds for comparison or other logic
        bot_headers = {'Authorization': f'Bot {str(baxi_tocken)}'}
        bot_guilds_response = requests.get(f'{API_ENDPOINT}/users/@me/guilds', headers=bot_headers)
        bot_guilds_response.raise_for_status()
        bot_guilds = bot_guilds_response.json()

        common_guilds = [guild for guild in user_guilds if guild in bot_guilds]

        # Prepare guild details
        guild_details = []
        for guild in common_guilds:
            guild_id = guild['id']
            guild_info_response = requests.get(f'{API_ENDPOINT}/guilds/{guild_id}?with_counts=true', headers=bot_headers)
            guild_info_response.raise_for_status()
            guild_info = guild_info_response.json()
            owner_info_response = requests.get(f'{API_ENDPOINT}/users/{guild_info.get("owner_id")}', headers=bot_headers)
            owner_info_response.raise_for_status()
            owner_info = owner_info_response.json()

            guild_details.append({
                'name': guild_info['name'],
                'id': guild_info['id'],
                'icon_url': f'https://cdn.discordapp.com/icons/{guild_info["id"]}/{guild_info["icon"]}.png' if guild_info['icon'] else DEFAULT_ICON,
                'member_count': guild_info.get('approximate_member_count', 'Unknown'),
                'owner_username': owner_info.get('username', 'Unknown'),
                'region': guild_info.get('region', 'Unknown'),
                'description': guild_info.get('description', 'No description available'),
                'verification_level': guild_info.get('verification_level', 'Unknown'),
            })

    except requests.RequestException as e:
        log_error(f"Request error: {e}")
        return "An error occurred while retrieving data. Please try again later."
    except Exception as e:
        log_error(f"Unexpected error: {e}")
        return "An unexpected error occurred. Please try again later."

    return await render_template('dashboard.html', guild_details=guild_details, api_key=str(config.get("BAXI", "api_key")))


@app.route('/dashboard-menu.json')
async def menu():
    return await send_from_directory('templates', 'dashboard-menu.json')

API_KEY = "bdash-X_KzUaBBMlM8d5a5xbAav4Z6bYqS3rnBN94ugjtkhsI"

@app.route("/api/module/<module_id>/<guild_id>", methods=["GET"])
async def load_module(module_id, guild_id):
    menu_data = {
        "anti_raid": {
            "load": f"https://baxi-backend.pyropixle.com/api/dash/settings/load/anti_raid/{guild_id}",
            "save": f"https://baxi-backend.pyropixle.com/api/dash/settings/save/anti_raid/{guild_id}"
        },
        "Minigame guessing": {
            "load": f"https://baxi-backend.pyropixle.com/api/dash/settings/load/mgg/{guild_id}",
            "save": f"https://baxi-backend.pyropixle.com/api/dash/settings/save/mgg/{guild_id}"
        },
        "countgame_data": {
            "load": f"https://baxi-backend.pyropixle.com/api/dash/settings/load/mgc/{guild_id}",
            "save": f"https://baxi-backend.pyropixle.com/api/dash/settings/save/mgc/{guild_id}"
        }
    }

    if module_id not in menu_data:
        return jsonify({"error": "Modul nicht gefunden"}), 404

    load_url = menu_data[module_id]["load"]

    # API-Key in den Header einfügen
    headers = {
        "Authorization": f"{API_KEY}"
    }

    try:
        response = requests.get(load_url, headers=headers)
        # Fehlerbehandlung analog zu JavaScript
        if not response.ok:
            response.raise_for_status()
        dataraw = response.json()
        return jsonify(dataraw)
        
    except requests.HTTPError as http_err:
        print(f"HTTP-Fehler: {http_err}")
        return jsonify({"error": "Fehler beim Abrufen der Daten"}), 500
    except Exception as err:
        print(f"Fehler: {err}")
        return jsonify({"error": "Fehler beim Abrufen der Daten"}), 500

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")
