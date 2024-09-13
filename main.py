import json, os, requests, configparser
from cryptography.fernet import Fernet
from quart import Quart, render_template, request, send_from_directory, jsonify, redirect, session
from quart_cors import cors
from assets.get_data import Get_Data

config = configparser.ConfigParser()
config.read("config/runtime.conf")

app = Quart(__name__, template_folder="web")
app = cors(app)
app.secret_key = os.urandom(24)

baxi_data = Get_Data(encryption_key=config.get("BAXI", "encryption_key"), api_key=config.get("BAXI", "baxi_info_key")).baxi_data_pull()


