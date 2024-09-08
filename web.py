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
baxi_data = baxi_data_request.json()

baxi_client_secret = f"{fernet.decrypt(baxi_data['client_secret']).decode()}"
baxi_tocken = f"{fernet.decrypt(baxi_data['tocken']).decode()}"

# Define the maintenance variable
maintenance = False  # Change to True when maintenance mode is active

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

@app.route("/dashboard")
async def dashboard():
    if 'token' not in session:
        return redirect('/login')

    headers = {
        'Authorization': f'Bearer {session["token"]}'
    }

    # Fetch user information
    user_info_response = requests.get(f'{API_ENDPOINT}/users/@me', headers=headers)
    user_info_response.raise_for_status()
    user_info = user_info_response.json()
    user_id = user_info['id']

    # Check maintenance mode
    if maintenance:
        # Fetch permissions array from external API only in maintenance mode
        perms_response = requests.get(PERMS_API)
        perms_response.raise_for_status()
        permitted_user_ids = perms_response.json()  # This should be a list of IDs

        # Check if the user ID is in the permitted list
        if int(user_id) not in permitted_user_ids:
            ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
            log_denied_access(ip_address, user_id)
            return "Access Denied: You do not have permission to access this dashboard during maintenance."
    else:
        # No restrictions outside of maintenance mode
        print(f"Access granted for user {user_id} (Maintenance: {maintenance})")

    # Fetch user guilds
    user_guilds_response = requests.get(f'{API_ENDPOINT}/users/@me/guilds', headers=headers)
    user_guilds_response.raise_for_status()
    user_guilds = user_guilds_response.json()

    bot_headers = {
        'Authorization': f'Bot {str(baxi_tocken)}'
    }
    bot_guilds_response = requests.get(f'{API_ENDPOINT}/users/@me/guilds', headers=bot_headers)
    bot_guilds_response.raise_for_status()
    bot_guilds = bot_guilds_response.json()

    common_guilds = []
    for user_guild in user_guilds:
        permissions = int(user_guild['permissions'])
        if permissions & 0x8:
            for bot_guild in bot_guilds:
                if user_guild['id'] == bot_guild['id']:
                    common_guilds.append(user_guild)
                    break

    guild_details = []
    for guild in common_guilds:
        guild_id = guild['id']
        guild_info_response = requests.get(f'{API_ENDPOINT}/guilds/{guild_id}?with_counts=true', headers=bot_headers)
        guild_info_response.raise_for_status()
        guild_info = guild_info_response.json()

        owner_id = guild_info.get('owner_id')
        owner_info_response = requests.get(f'{API_ENDPOINT}/users/{owner_id}', headers=bot_headers)
        owner_info_response.raise_for_status()
        owner_info = owner_info_response.json()
        owner_username = owner_info.get('username', 'Unknown')

        guild_details.append({
            'name': guild_info['name'],
            'id': guild_info['id'],
            'icon_url': f'https://cdn.discordapp.com/icons/{guild_info["id"]}/{guild_info["icon"]}.png' if guild_info['icon'] else DEFAULT_ICON,
            'member_count': guild_info.get('approximate_member_count', 'Unknown'),
            'owner_username': owner_username,
            'region': guild_info.get('region', 'Unknown'),
            'description': guild_info.get('description', 'No description available'),
            'verification_level': guild_info.get('verification_level', 'Unknown'),
        })

    return await render_template('dashboard.html', guild_details=guild_details)

@app.route('/dashboard-menu.json')
async def menu():
    return await send_from_directory('templates', 'dashboard-menu.json')
EXTERNAL_API_KEY = "bdash-X_KzUaBBMlM8d5a5xbAav4Z6bYqS3rnBN94ugjtkhsI"

@app.route("/api/data", methods=["GET"])
async def get_api_data():
    endpoint = request.args.get('endpoint')
    
    if not endpoint:
        return jsonify({"error": "No endpoint provided"}), 400
    
    headers = {
        'Authorization': f'Bearer {EXTERNAL_API_KEY}'  # Include the API key here
    }
    
    try:
        response = requests.get(endpoint, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        # Process data if needed
        def replace_value(data, old, new):
            if isinstance(data, dict):
                return {k: replace_value(v, old, new) for k, v in data.items()}
            elif isinstance(data, list):
                return [replace_value(i, old, new) for i in data]
            elif data == old:
                return new
            return data

        processed_data = replace_value(data, None, "null")
        return jsonify(processed_data)
    
    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")
