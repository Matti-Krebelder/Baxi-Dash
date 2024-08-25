import json

from flask import Flask, request, redirect, session, render_template, send_from_directory
import requests
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

CLIENT_ID = '1277310867381158002'
CLIENT_SECRET = '4doXCvWpIxOXeQTtxnkPPw9O7MNB-pV7'
REDIRECT_URI = 'http://127.0.0.1:5000/callback'
API_ENDPOINT = 'https://discord.com/api/v10'
AUTH_URL = 'https://discord.com/api/oauth2/authorize'
TOKEN_URL = 'https://discord.com/api/oauth2/token'
BOT_TOKEN = 'MTI3NzMxMDg2NzM4MTE1ODAwMg.GL6Hjb.H8CWb5QTquw_42LG6zdOjeBi8kGrzRBe1mtUpM'

@app.route("/")
def home():
    return '<a href="/login">Login with Discord</a>'

@app.route("/login")
def login():
    return redirect(f'{AUTH_URL}?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code&scope=identify%20guilds%20email')

@app.route("/callback")
def callback():
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
def dashboard():
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

    return render_template('dashboard.html', guild_details=guild_details)

@app.route('/dashboard-menu.json')
def menu():
    return send_from_directory('templates', 'dashboard-menu.json')

if __name__ == '__main__':
    app.run(debug=True)
