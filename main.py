import configparser
import os
import secrets

import requests
from quart import (
    Quart,
    render_template,
    request,
    jsonify,
    redirect,
    session,
)
from quart_cors import cors
from reds_simple_logger import Logger  # type: ignore

import assets.get_guilds as get_guilds
from assets.get_data import Get_Data, get_active_systems

logger = Logger()

config = configparser.ConfigParser()
config.read("config/runtime.conf")

app = Quart(__name__, template_folder="web")
app = cors(app)
app.secret_key = os.urandom(24)

maintenance = config.getboolean("DASH", "maintenance")

baxi_data = Get_Data(
    encryption_key=config.get("BAXI", "encryption_key"),
    api_key=config.get("BAXI", "baxi_info_key"),
).baxi_data_pull()

logger.debug.info("Logged in as " + baxi_data.app_name)


@app.route("/api/module-data", methods=["GET"])
async def get_module_data():
    api_endpoint = request.args.get("apiEndpoint")
    guild_id = request.args.get("guildId")
    api_key = config["BAXI"]["api_key"]

    if not api_endpoint or not guild_id:
        return jsonify({"error": "Missing apiEndpoint or guildId"}), 400

    csrf_token = session.get('csrf_token')

    data = {"csrf_token": csrf_token}

    full_api_endpoint = f"https://baxi-backend.pyropixle.com/api/dash/settings/load/{api_endpoint}/{guild_id}"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"{api_key}",
    }

    request_user = requests.get(full_api_endpoint, headers=headers, json=data)
    return request_user.json()


@app.route("/api/module-save", methods=["POST"])
async def save_module_data():
    data = await request.get_json()
    api_endpoint = data.get("apiEndpoint")
    guild_id = data.get("guildId")
    module_data = data.get("data")
    api_key = config["BAXI"]["api_key"]

    csrf_token = session.get('csrf_token')
    module_data["csrf_token"] = csrf_token
    if not api_endpoint or not guild_id or not module_data:
        return jsonify({"error": "Missing apiEndpoint, guildId or data"}), 400

    full_api_endpoint = f"https://baxi-backend.pyropixle.com/api/dash/settings/save/{api_endpoint}/{guild_id}"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"{api_key}",
    }
    response = requests.post(full_api_endpoint, json=module_data, headers=headers)
    return response.json()


@app.route("/login")
async def login():
    if "token" in session:
        return redirect("/")
    return redirect(
        f'{config["ENDPOINT"]["auth"]}?client_id={int(baxi_data.client_id)}&redirect_uri={baxi_data.redirect_uri}&response_type=code&scope=identify%20guilds'
    )


@app.route("/logout")
async def logout():
    if "token" in session:
        session.clear()
        return await render_template("logout.html", version=config["DASH"]["version"],
                                     dashboardmessage=config["DASH"]["dashboardmessage"])
    else:
        return redirect("/")


@app.route("/callback")
async def callback():
    code = request.args.get("code")
    data = {
        "client_id": int(baxi_data.client_id),
        "client_secret": str(baxi_data.client_secret),
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": str(baxi_data.redirect_uri),
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    r = requests.post(config["ENDPOINT"]["tocken"], data=data, headers=headers)
    logger.debug.info(r.text)
    r.raise_for_status()
    session["token"] = r.json()["access_token"]
    return redirect("/")


@app.route("/dashboard")
async def dash_send_to_new_dash():
    return redirect("/")


@app.route("/")
async def dash():
    MANAGE_GUILD_PERMISSION = 0x0000000000000020
    if "token" not in session:
        return await render_template("login.html", version=config["DASH"]["version"],
                                     dashboardmessage=config["DASH"]["dashboardmessage"])
    try:
        user_guilds = get_guilds.get_user_guilds(
            session["token"], config["ENDPOINT"]["discord_api"]
        )
        bot_guilds = get_guilds.get_bot_guilds(
            baxi_data.token, config["ENDPOINT"]["discord_api"]
        )

        bot_guild_ids = {guild["id"] for guild in bot_guilds}

        # Gemeinsame Gilden finden, bei denen der Benutzer "Manage Guild" Rechte hat
        common_guilds = [
            guild for guild in user_guilds
            if guild["id"] in bot_guild_ids and
               (int(guild["permissions"]) & MANAGE_GUILD_PERMISSION) == MANAGE_GUILD_PERMISSION
        ]
        logger.debug.info(common_guilds)
        guild_details = []
        bot_headers = {"Authorization": f"Bot {str(baxi_data.token)}"}
        for guild in common_guilds:
            active_systems = get_active_systems(key=config["BAXI"]["api_key"], guild_id=int(guild["id"]))
            guild_id = guild["id"]
            guild_info_response = requests.get(
                f'{config["ENDPOINT"]["discord_api"]}/guilds/{guild_id}?with_counts=true',
                headers=bot_headers,
            )
            guild_info = guild_info_response.json()
            owner_info_response = requests.get(
                f'{config["ENDPOINT"]["discord_api"]}/users/{guild_info.get("owner_id")}',
                headers=bot_headers,
            )
            owner_info = owner_info_response.json()
            data = {
                "name": guild_info["name"],
                "id": guild_info["id"],
                "icon_url": (
                    f'https://cdn.discordapp.com/icons/{guild_info["id"]}/{guild_info["icon"]}.png'
                    if guild_info["icon"]
                    else config["DASH"]["default_icon"]
                ),
                "member_count": guild_info.get(
                    "approximate_member_count", "Unknown"
                ),
                "owner_username": owner_info.get("username", "Unknown"),
                "region": guild_info.get("region", "Unknown"),
                "description": guild_info.get(
                    "description", "No description available"
                ),
                "verification_level": guild_info.get(
                    "verification_level", "Unknown"
                ),
                "active_systems": active_systems
            }
            guild_details.append(data)
            logger.debug.info(data)
        return await render_template(
            "dashboard.html",
            guild_details=guild_details,
            version=config["DASH"]["version"],
            dashboardmessage=config["DASH"]["dashboardmessage"]
        )

    except Exception as e:
        logger.error('Error in app.route("/"): ' + str(e))
        return jsonify({"notify-error": f"Error: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0")
