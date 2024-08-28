import json

from quart import Quart, render_template, request, send_from_directory, send_file, jsonify, url_for, redirect, session, make_response
from quart_cors import cors

import requests
import os

app = Quart(__name__, template_folder="Templates")
app = cors(app)
app.secret_key = os.urandom(24)

CLIENT_ID = '981268814308184084'
CLIENT_SECRET = "2KbKKJO0UEIwMasUVm5znMR4Z2D8qyTo"
REDIRECT_URI = 'https://baxi.pyropixle.com/callback'
API_ENDPOINT = 'https://discord.com/api/v10'
AUTH_URL = 'https://discord.com/api/oauth2/authorize'
TOKEN_URL = 'https://discord.com/api/oauth2/token'
BOT_TOKEN = 'OTgxMjY4ODE0MzA4MTg0MDg0.GMCiT4.EERN07N-94eV_vGTvP0AEvcEFJDBCgXEurfSRk'

@app.route("/")
async def home():
    return '<a href="/login">Login with Discord</a>'

@app.route("/login")
async def login():
    return redirect(f'{AUTH_URL}?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code&scope=identify%20guilds%20email')

@app.route("/callback")
async def callback():
    code = request.args.get('code')
    data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    r = requests.post(TOKEN_URL, data=data, headers=headers)
    r.raise_for_status()
    session['token'] = r.json()['access_token']
    return redirect('/dashboard')

DEFAULT_ICON = 'https://cdn.discordapp.com/embed/avatars/0.png'

@app.route("/dashboard")
async def dashboard():
    global APIKEY
    if 'token' not in session:
        return redirect('/login')

    headers = {
        'Authorization': f'Bearer {session["token"]}'
    }

    user_guilds_response = requests.get(f'{API_ENDPOINT}/users/@me/guilds', headers=headers)
    user_guilds_response.raise_for_status()
    user_guilds = user_guilds_response.json()

    bot_headers = {
        'Authorization': f'Bot {BOT_TOKEN}'
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

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")
