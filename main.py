import json, os, requests, configparser
from cryptography.fernet import Fernet
from quart import Quart, render_template, request, send_from_directory, jsonify, redirect, session
from quart_cors import cors
from reds_simple_logger import Logger

from assets.get_data import Get_Data
import assets.get_guilds as get_guilds

logger = Logger()

config = configparser.ConfigParser()
config.read("config/runtime.conf")

app = Quart(__name__, template_folder="web")
app = cors(app)
app.secret_key = os.urandom(24)

maintenance = config.getboolean("DASH", "maintenance")

baxi_data = Get_Data(encryption_key=config.get("BAXI", "encryption_key"), api_key=config.get("BAXI", "baxi_info_key")).baxi_data_pull()

@app.route("/login")
async def login():
    if "tocken" in session:
        return redirect("/")
    return redirect(f'{config["ENDPOINT"]["auth"]}?client_id={int(baxi_data.client_id)}&redirect_uri={baxi_data.redirect_uri}&response_type=code&scope=identify%20guilds')


@app.route("/callback")
async def callback():
    code = request.args.get('code')
    data = {
        'client_id': int(baxi_data.client_id),
        'client_secret': str(baxi_data.client_secret),
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': str(baxi_data.redirect_uri)
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    r = requests.post(config["ENDPOINT"]["tocken"], data=data, headers=headers)
    logger.debug.info(r.text)
    r.raise_for_status()
    session['token'] = r.json()['access_token']
    return redirect('/')

@app.route("/")
async def dash():
    if "token" not in session:
        return redirect("/login")
    
    try:
        user_guilds = get_guilds.get_user_guilds(session["token"], config["ENDPOINT"]["discord_api"])
        bot_guilds = get_guilds.get_bot_guilds(baxi_data.tocken, config["ENDPOINT"]["discord_api"])
        common_guilds = [guild for guild in user_guilds if guild in bot_guilds]
        
        guild_details = []
        bot_headers = {'Authorization': f'Bot {str(baxi_data.tocken)}'}
        for guild in common_guilds:
            guild_id = guild['id']
            guild_info_response = requests.get(f'{config["ENDPOINT"]["discord_api"]}/guilds/{guild_id}?with_counts=true', headers=bot_headers)
            guild_info_response.raise_for_status()
            guild_info = guild_info_response.json()
            owner_info_response = requests.get(f'{config["ENDPOINT"]["discord_api"]}/users/{guild_info.get("owner_id")}', headers=bot_headers)
            owner_info_response.raise_for_status()
            owner_info = owner_info_response.json()
            
            guild_details.append({
                'name': guild_info['name'],
                'id': guild_info['id'],
                'icon_url': f'https://cdn.discordapp.com/icons/{guild_info["id"]}/{guild_info["icon"]}.png' if guild_info['icon'] else config["DASH"]["default_icon"],
                'member_count': guild_info.get('approximate_member_count', 'Unknown'),
                'owner_username': owner_info.get('username', 'Unknown'),
                'region': guild_info.get('region', 'Unknown'),
                'description': guild_info.get('description', 'No description available'),
                'verification_level': guild_info.get('verification_level', 'Unknown'),
            })
        logger.debug.info(guild_details)
        return await render_template('dashboard.html', guild_details=guild_details)
            
        
    except Exception as e:
        logger.error("Error in app.route(\"/\"): " + str(e))
        return "An error occured!", 500
        
    

if __name__ == '__main__':
    app.run(debug=False, host="0.0.0.0")